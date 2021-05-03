# RefMan - A Simple python-based reference manager.
# Author: Adrian Caruana (adrian@adriancaruana.com)
import argparse
from arxiv2bib import arxiv2bib
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
    META_NAME,
    BIBTEX_NAME,
    CROSSREF_URL,
    ARXIV_PDF_URL,
    FMT_BIBTEX,
    FMT_CITEPROC,
)
from ._utils import md5_hexdigest, is_valid_url, is_valid_doi, fix_arxiv2bib_fmt
from ._scihub import SciHub

STATUS_HANDLER = None
LOGGER = logging.getLogger(f"refman.{__name__}")
LOGGER.setLevel(logging.INFO)
SH = SciHub()


def update_status(msg: str, level_attr: str = 'info'):
    global STATUS_HANDLER
    if not isinstance(STATUS_HANDLER, tqdm):
        LOGGER.__getattr__(level_attr).__call__(msg)
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
    meta_name: str = dataclasses.field(init=False, default=META_NAME)
    bibtex_name: str = dataclasses.field(init=False, default=BIBTEX_NAME)

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
    def new_paper_from_arxiv(cls, arxiv: str):
        """Adds a new paper to the `papers` dir from an arxiv str"""
        update_status(f"{arxiv=}: Retrieving bibtex entry.")
        bib_str = fix_arxiv2bib_fmt(arxiv2bib([arxiv])[0])
        meta = dict(bibtexparser.loads(bib_str).entries[0])
        update_status(f"{arxiv=}: Retrieving PDF.")
        pdf_data = requests.get(ARXIV_PDF_URL.format(arxiv=arxiv)).content
        paper = cls(meta=meta, bibtex=bib_str, pdf_data=pdf_data)
        paper.to_disk()
        return paper

    @classmethod
    def new_paper_from_doi(cls, doi: str, pdf: str = None):
        """Adds a new paper to the `papers` dir from a DOI"""
        # Fetch the reference data from cross-ref
        if not is_valid_doi(doi):
            raise ValueError(f"Provided {doi=} is not a valid DOI.")
        update_status(f"{doi=}: Retrieving structured reference info.")
        r = requests.get((url := CROSSREF_URL.format(doi=doi, fmt=FMT_CITEPROC)))
        if not r.ok:
            raise ValueError(
                "Could not get citeproc+json from crossref.\n"
                f"HTTP Response: {r.status_code}\nDOI: {doi}\nURL: {url}"
            )
        citeproc_json = dict(r.json())
        update_status(f"{doi=}: Retrieving bibtex entry.")
        bib_str = requests.get(
            CROSSREF_URL.format(doi=doi, fmt=FMT_BIBTEX)
        ).content.decode("utf-8")
        update_status(f"{doi=}: Retrieving PDF.")
        pdf_data = None
        if pdf is not None:
            pdf_data = cls._get_pdf_data_from_path(pdf_path=pdf)
        if pdf_data is None:
            pdf_data = cls._get_pdf_data_from_doi(doi, citeproc_json)
        meta = dict(bibtexparser.loads(bib_str).entries[0])
        paper = cls(meta=meta, bibtex=bib_str, pdf_data=pdf_data)
        paper.to_disk()
        return paper

    @classmethod
    def new_paper_from_bibtex(
        cls,
        bibtex_str: str,
        pdf_path: str = None,
        key: str = None,
    ):
        """Adds a new paper to the `papers` dir from a bibtex_str.
        Optionally: Associate a pdf with the paper via local path or url
        """
        bib = bibtexparser.loads(bibtex_str)
        if not bib.entries[0].get("DOI", False):
            bib.entries[0]["DOI"] = ""
        if key is not None:
            bib.entries[0]["ID"] = key
            bibtex_str = bibtexparser.dumps(bib)
        meta = dict(bib.entries[0])
        bibtex_key = cls._bibtex_key_from_bibtex_str(meta)
        LOGGER.info(f"{bibtex_key}: Parsing BibTeX string.")
        pdf_data = None
        if pdf_data is not None:
            pdf_data = cls._get_pdf_data_from_path(pdf_path)
        paper = Paper(meta=meta, bibtex=bibtex_str, pdf_data=pdf_data)
        paper.to_disk()
        return paper

    @classmethod
    def _get_pdf_data_from_path(cls, pdf_path: str) -> bytes:
        pdf_data = None
        if is_valid_url(pdf_path):
            r = requests.get(pdf_path)
            if "application/pdf" not in r.headers["Content-Type"]:
                LOGGER.warning(f"{bibtex_key}: {pdf_path} did not contain a PDF.")
                pdf_data = None
            else:
                LOGGER.info(f"{bibtex_key}: Got PDF from URL.")
                pdf_data = r.content
        else:
            if pdf_path is not None and Path(pdf_path).exists():
                with open(pdf_path, "r") as f:
                    LOGGER.info(f"{bibtex_key}: Got PDF from DISK.")
                    pdf_data = f.read()
        
        return pdf_data

    @classmethod
    def _get_pdf_data_from_doi(cls, doi: str, citeproc_json: dict) -> bytes:
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
                update_status(f"{doi=}: Got PDF from CITEPROC.")
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
            update_status(f"{doi=}: Got PDF from SCI-HUB.")
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
        return list(map(lambda x: x.parent, REFMAN_DIR.rglob(META_NAME)))

    def _get_paper_meta(self, paper) -> dict:
        return {
            "doi": paper.meta.get("doi", ""),  # For parsing via DOI
            "eprint": paper.meta.get("eprint", ""),  # For parsing via arxiv
            "bibtex_path": str(paper.bibtex_path),
            "bibtex_key": str(paper._bibtex_key),
        }

    def append_to_db(self, paper: Paper):
        self.db = self.db.append(self._get_paper_meta(paper), ignore_index=True)

    def add_using_arxiv(self, arxiv: str):
        if arxiv is not None and arxiv not in list(self.db.get("eprint", list())):
            self.append_to_db(Paper.new_paper_from_arxiv(arxiv))

        self._update_db()

    def add_using_doi(self, doi: str, pdf: str):
        if (
                doi is not None and
                doi.lower() not in map(
                    lambda x: x.lower(),
                    self.db.get("doi", list())
                )
        ):
            self.append_to_db(Paper.new_paper_from_doi(doi, pdf))

        self._update_db()

    def add_using_bibtex(
            self,
            bibtex_str: str,
            pdf_path: str,
            key: str = None
    ):
        paper = Paper.new_paper_from_bibtex(
            bibtex_str=bibtex_str,
            pdf_path=pdf_path,
            key=key
        )
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
        ),
        type=str,
        required=False,
        default=None,
    )
    parser.add_argument(
        "-a",
        "--arxiv",
        help=(
            "Gets the paper from an Arxiv reference string. "
        ),
        type=str,
        required=False,
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
    parser.add_argument(
        "-k",
        "--key",
        help=(
            "Explicitly define the key to use (without hash) for the paper."
        ),
        type=str,
        default=None,
    )
    args = parser.parse_args()
    if bool(args.arxiv) and bool(args.pdf):
        raise ValueError(
            f"`-p, --pdf` cannot be used with `-a, --arxiv`."
        )

    if not os.getenv("REFMAN_DATA", False):
        LOGGER.warning(
            f"`REFMAN_DATA` not found in environment variables. Using '{REFMAN_DIR}' as data path."
        )
    REFMAN_DIR.mkdir(exist_ok=True, parents=True)

    refman = RefMan()
    if bool(args.arxiv):
        for job_kwargs in progress_with_status([{'arxiv': args.arxiv}]):
            refman.add_using_arxiv(**job_kwargs)
    if bool(args.doi):
        for job_kwargs in progress_with_status([{'doi': args.doi, 'pdf': args.pdf}]):
            refman.add_using_doi(**job_kwargs)
    if bool(args.bibtex):
        for job_kwargs in progress_with_status(
                [{'bibtex_str': args.bibtex, 'pdf_path': args.pdf, 'key': args.key}]
        ):
            refman.add_using_bibtex(**job_kwargs)


if __name__ == "__main__":
    main()
