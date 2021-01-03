# RefMan - A Simple python-based reference manager.
# Author: Adrian Caruana (adrian@adriancaruana.com)
import argparse
import bibtexparser
import dataclasses
import hashlib
import json
import logging
import os
import pandas as pd
from pathlib import Path
import re
import requests
from tqdm import tqdm
from typing import Iterable, List, Tuple

from ._constants import (
    REFMAN_DIR,
    PAPER_DIR,
    BIB_DB,
    BIB_REF,
    CROSSREF_URL,
    FMT_BIBTEX,
    FMT_CITEPROC,
)
from ._utils import md5_hexdigest, is_valid_url
from ._scihub import SciHub

STATUS_HANDLER = None
LOGGER = logging.getLogger(f"refman.{__name__}")
LOGGER.setLevel(logging.INFO)
SH = SciHub()


def update_status(msg: str):
    global STATUS_HANDLER
    if not isinstance(STATUS_HANDLER, tqdm):
        LOGGER.info(msg)
        return
    STATUS_HANDLER.set_postfix_str(msg)


def progress_with_status(it: Iterable):
    global STATUS_HANDLER
    ncols = str(min(len(it), 20))
    barfmt = "{l_bar}{bar:" + ncols + "}{r_bar}{bar:-" + ncols + "b}"
    return (STATUS_HANDLER := tqdm(it, bar_format=barfmt))


@dataclasses.dataclass
class Paper:
    meta: dict
    bibtex: str
    pdf_data: bytes = dataclasses.field(default=None)
    meta_name: str = "meta.json"
    bibtex_name: str = ".bib"

    def __post_init__(self):
        self.paper_path.mkdir(exist_ok=True, parents=True)

    @property
    def paper_path(self):
        return REFMAN_DIR / "_".join((self._bibtex_key, md5_hexdigest(self.bibtex)[:7]))

    @property
    def meta_path(self):
        return self.paper_path / self.meta_name

    @property
    def bibtex_path(self):
        return self.paper_path / self.bibtex_name

    @property
    def pdf_path(self):
        return self.paper_path / (self._bibtex_key + ".pdf")

    @property
    def _bibtex_key(self) -> str:
        return self._bibtex_key_from_bibtex_str(self.meta)

    @classmethod
    def _bibtex_key_from_bibtex_str(cls, meta: dict):
        return meta.get("ID")

    @classmethod
    def parse_from_disk(cls, paper_path: Path, read_pdf: bool = False):
        """Returns a `Paper` object from disk."""
        update_status(f"{paper_path}: Loading reference from disk.")
        with open(paper_path / cls.meta_name, "r") as f:
            meta = json.load(f)
        with open(paper_path / cls.bibtex_name, "r") as f:
            bibtex = f.read()
        pdf_data = None
        if read_pdf:
            try:
                pdf_path = next(paper_path.glob("*.pdf"))
                update_status(f"{paper_path}: Found {pdf_path.name}.")
            except StopIteration as e:
                update_status(f"{paper_path}: No PDF found.")
            with open(paper_path / pdf_path, "wb") as f:
                pdf_data = f.read()
        return cls(meta=meta, bibtex=bibtex, pdf_data=pdf_data)

    @classmethod
    def new_paper_from_doi(cls, doi: str):
        """Adds a new paper to the `papers` dir from a DOI"""
        # Fetch the reference data from cross-ref
        update_status(f"{doi=}: Retrieving structured reference info.")
        citeproc_json = dict(
            requests.get(CROSSREF_URL.format(doi=doi, fmt=FMT_CITEPROC)).json()
        )
        update_status(f"{doi=}: Retrieving bibtex entry.")
        bib_str = requests.get(
            CROSSREF_URL.format(doi=doi, fmt=FMT_BIBTEX)
        ).content.decode("utf-8")
        update_status(f"{doi=}: Retrieving PDF.")
        pdf_data = cls._get_pdf_data(doi, citeproc_json)
        meta = dict(bibtexparser.loads(bib_str).entries[0])
        paper = cls(meta=meta, bibtex=bib_str, pdf_data=pdf_data)
        paper.to_disk()
        return paper

    @classmethod
    def new_paper_from_bibtex(
        cls,
        bibtex_str: str,
        pdf_path: str = None,
    ):
        """Adds a new paper to the `papers` dir from a bibtex_str.
        Optionally: Associate a pdf with the paper via local path or url
        """
        meta = dict(bibtexparser.loads(bibtex_str).entries[0])
        bibtex_key = cls._bibtex_key_from_bibtex_str(meta)
        LOGGER.info(f"{bibtex_key}: Parsing BibTeX string.")
        pdf_data = None
        if is_valid_url(pdf_path):
            r = requests.get(pdf_path)
            if "application/pdf" not in r.headers["Content-Type"]:
                LOGGER.warning(f"{bibtex_key}: {pdf_path} did not contain a PDF.")
                pdf_data = None
            else:
                LOGGER.info(f"{bibtex_key}: Got PDF.")
                pdf_data = r.content
        else:
            if pdf_path is not None and Path(pdf_path).exists():
                with open(pdf_path, "r") as f:
                    LOGGER.info(f"{bibtex_key}: Reading PDF.")
                    pdf_data = f.read()
        paper = Paper(meta=meta, bibtex=bibtex_str, pdf_data=pdf_data)
        paper.to_disk()
        return paper

    @classmethod
    def _get_pdf_data(cls, doi: str, citeproc_json: dict) -> bytes:
        # Try to download from other available sources before sci-hub
        if "link" in citeproc_json.keys():
            update_status(f"{doi=}: Found PDF link from crossref, attempting download.")
            try:
                link = next(
                    l["URL"]
                    for l in citeproc_json["link"]
                    if l["content-type"] == "application/pdf"
                )
                r = requests.get(link)
                if "application/pdf" not in r.headers["Content-Type"]:
                    raise TypeError(f"Link did not contain a PDF.")
                update_status(f"{doi=}: Got PDF.")
                return r.content
            except StopIteration as e:
                update_status(
                    f"{doi=}: While citeproc+json contains link(s), none link to a PDF."
                )
            except Exception as e:
                update_status(
                    f"{doi=}: Could not get PDF from citeproc+json. "
                    f"Reason: {str(e)}"
                )
        # Download the PDF using sci-hub
        update_status(f"{doi=}: Falling back to sci-hub for PDF retrieval.")
        try:
            pdf_data = SH.fetch(doi)["pdf"]
            update_status(f"{doi=}: Got PDF.")
            return pdf_data
        except Exception as e:
            LOGGER.warning(
                f"For {doi=}: Failed to get PDF from sci-hub. No PDF available."
                f"Reason: {str(e)}"
            )
        return bytes()

    def to_disk(self):
        with open(self.meta_path, "w") as f:
            json.dump(self.meta, f)
        with open(self.bibtex_path, "w") as f:
            f.write(self.bibtex)
        if self.pdf_data is not None:
            with open(self.pdf_path, "wb") as f:
                f.write(self.pdf_data)


@dataclasses.dataclass
class RefMan:
    db: pd.DataFrame = dataclasses.field(init=False, default=None)

    def __post_init__(self):
        LOGGER.info("Parsing database.")
        paper_paths = self._paper_paths_list()
        if len(paper_paths) > 0:
            path_it = progress_with_status(paper_paths)
            papers = list(map(Paper.parse_from_disk, path_it))
            self.db = pd.DataFrame(map(self._get_paper_meta, papers))
        else:
            self.db = pd.DataFrame(None)

    def _paper_paths_list(self):
        return list(filter(lambda x: not x.is_file(), REFMAN_DIR.glob("*")))

    def _get_paper_meta(self, paper) -> dict:
        return {
            "doi": paper.meta.get("doi", None),
            "bibtex_path": str(paper.bibtex_path),
            "bibtex_key": str(paper._bibtex_key),
        }

    def append_to_db(self, paper: Paper):
        self.db = self.db.append(self._get_paper_meta(paper), ignore_index=True)

    def add_using_doi(self, doi: List[str]):
        if doi is not None:
            doi_li = list(self.db.get("doi", list()))
            to_append = list(filter(lambda x: x not in doi_li, doi))
            if not to_append:
                LOGGER.warning(
                    "No papers to add to the database (they already exist!). Finishing."
                )
                return
            paper_it = progress_with_status(to_append)
            papers = list(map(Paper.new_paper_from_doi, paper_it))
            for paper in papers:
                self.append_to_db(paper)
        self._update_db()

    def add_using_bibtex(self, bibtex_str: str, pdf_path: Path):
        paper = Paper.new_paper_from_bibtex(bibtex_str=bibtex_str, pdf_path=pdf_path)
        self.append_to_db(paper)
        self._update_db()

    def _update_db(self):
        # Write out bibliography file
        LOGGER.info(f"Writing bibliography file to '{BIB_REF}'.")
        with open(BIB_REF, "w") as f:
            for paper_bibtex in self.db["bibtex_path"]:
                f.write(open(paper_bibtex, "r").read() + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="RefMan - A Simple python-based reference manager."
    )
    parser.add_argument(
        "-d",
        "--doi",
        help=(
            "Tries to find and download the paper using the DOI. "
            "Append multiple papers using a space-separated list"
        ),
        type=str,
        nargs="+",
        default=None,
    )
    parser.add_argument(
        "-b",
        "--bibtex",
        help=(
            "Adds an entry to the database from a bibtex-string. "
            "Optionally, provide -p, --pdf to associate this entry with a PDF."
        ),
        type=str,
        default=None,
    )
    parser.add_argument(
        "-p",
        "--pdf",
        help=(
            "Adds an entry to the database from a bibtex-string. "
            "Optionally, provide -p, --pdf to associate this entry with a PDF."
        ),
        type=str,
        default=None,
    )
    args = parser.parse_args()
    if not bool(args.doi) ^ (bool(args.bibtex) or bool(args.pdf)):
        raise ValueError(
            f"Please provide either `-d, -doi`, OR `-b, --bibtex`. "
            f"`-p, --pdf` can only be used with `-b, --bibtex`."
        )

    if not os.getenv("REFMAN_DATA", False):
        LOGGER.warning(
            f"`REFMAN_DATA` not found in environment variables. Using '{REFMAN_DIR}' as data path."
        )
    REFMAN_DIR.mkdir(exist_ok=True, parents=True)

    refman = RefMan()
    if bool(args.doi):
        refman.add_using_doi(doi=args.doi)
    if bool(args.bibtex):
        refman.add_using_bibtex(bibtex_str=args.bibtex, pdf_path=args.pdf)


if __name__ == "__main__":
    main()
