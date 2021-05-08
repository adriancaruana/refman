# RefMan - A Simple python-based reference manager.
# Author: Adrian Caruana (adrian@adriancaruana.com)
import argparse
import dataclasses
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import requests
import shutil
from typing import Iterable, List, Tuple

from arxiv2bib import arxiv2bib
import bibtexparser
import pandas as pd
import pyperclip
from tqdm import tqdm
import typer

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
LOGGER.setLevel(logging.DEBUG)
SH = SciHub()


APP = typer.Typer(help="RefMan - A Simple python-based reference manager.")


def update_status(msg: str, level_attr: str = 'info'):
    global STATUS_HANDLER
    if not isinstance(STATUS_HANDLER, tqdm):
        # LOGGER.__getattr__(level_attr)
        LOGGER.info(msg)
        return
    STATUS_HANDLER.set_postfix_str(msg)


def progress_with_status(it: Iterable):
    global STATUS_HANDLER
    ncols = str(min(len(it), 20))
    barfmt = "{l_bar}{bar:" + ncols + "}{r_bar}{bar:-" + ncols + "b}"
    return (STATUS_HANDLER := tqdm(it, bar_format=barfmt))

def reset_progress_status_handler():
    global STATUS_HANDLER
    STATUS_HANDLER = None


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
    def _update_bibtex_str_key(cls, bibtex_str: str, key: str):
        bib = bibtexparser.loads(bibtex_str)
        if not bib.entries[0].get("DOI", False):
            bib.entries[0]["DOI"] = ""
        bib.entries[0]["ID"] = key
        return bibtexparser.dumps(bib)

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
    def new_paper_from_arxiv(cls, arxiv: str, key: str = None):
        """Adds a new paper to the `papers` dir from an arxiv str"""
        update_status(f"{arxiv=}: Retrieving bibtex entry.")
        bib_str = fix_arxiv2bib_fmt(arxiv2bib([arxiv])[0])
        # Set custom key if requested
        if key is not None:
            bib_str = cls._update_bibtex_str_key(bib_str, key)
        meta = dict(bibtexparser.loads(bib_str).entries[0])
        update_status(f"{arxiv=}: Retrieving PDF.")
        pdf_data = requests.get(ARXIV_PDF_URL.format(arxiv=arxiv)).content
        paper = cls(meta=meta, bibtex=bib_str, pdf_data=pdf_data)
        paper.to_disk()
        return paper

    @classmethod
    def new_paper_from_doi(cls, doi: str, key: str = None, pdf: str = None):
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
        # Set custom key if requested
        if key is not None:
            bib_str = cls._update_bibtex_str_key(bib_str, key)
        # Prepare the Paper object
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
        # Set custom key if requested
        if key is not None:
            bibtex_str = cls._update_bibtex_str_key(bibtex_str, key)
        bib = bibtexparser.loads(bibtex_str)
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
        if not os.getenv("REFMAN_DATA", False):
            LOGGER.warning(
                f"`REFMAN_DATA` not found in environment variables. Using '{REFMAN_DIR}' as data path."
            )
        REFMAN_DIR.mkdir(exist_ok=True, parents=True)
        LOGGER.info("Parsing database.")
        paper_paths = self._paper_paths_list()
        if len(paper_paths) > 0:
            path_it = progress_with_status(paper_paths)
            papers = list(map(Paper.parse_from_disk, path_it))
            reset_progress_status_handler()
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

    def remove_from_db(self, column: str, value: str):
        self.db = self.db[self.db[column] != value]
        
    def add_using_arxiv(self, arxiv: str, key: str = None):
        if arxiv is not None and arxiv not in list(self.db.get("eprint", list())):
            paper = Paper.new_paper_from_arxiv(arxiv, key)
            self.append_to_db(paper)

        self._update_db()
        return paper.meta.get("ID", "")

    def add_using_doi(self, doi: str, pdf: str):
        if (
                doi is not None and
                doi.lower() not in map(
                    lambda x: x.lower(),
                    self.db.get("doi", list())
                )
        ):
            paper = Paper.new_paper_from_doi(doi, pdf)
            self.append_to_db(paper)

        self._update_db()
        return paper.meta.get("ID", "")

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
        return paper.meta.get("ID", "")

    def rekey(self, key: str, new_key: str):
        paper_path_li = list(REFMAN_DIR.glob(key + "*"))
        if len(paper_path_li) > 1:
            raise ValueError(f"Multiple papers matching wildcard: {key + '*'}.\n{paper_path_li=}.")
        if len(paper_path_li) == 0:
            raise FileNotFoundError(f"No papers matching wildcard: {key + '*'}. Exiting.")
        paper_path = paper_path_li[0]
        old_paper = Paper.parse_from_disk(paper_path)
        new_paper = Paper.new_paper_from_bibtex(
            bibtex_str=old_paper.bibtex,
            pdf_path=old_paper.pdf_path,
            key=new_key
        )
        # Remove the old paper
        self.remove_paper(key)
        return new_paper.meta.get("ID", "")

    def remove_paper(self, key: str):
        paper_path = REFMAN_DIR / key
        if not paper_path.exists():
            LOGGER.info(f"Couldn't find any paper at: {paper_path}. Trying wildcard...")
            paper_path_li = list(REFMAN_DIR.glob(key + "*"))
            if len(paper_path_li) > 1:
                raise ValueError(f"Multiple papers matching wildcard: {key + '*'}.\n{paper_path_li=}.")
            if len(paper_path_li) == 0:
                raise FileNotFoundError(f"No papers matching wildcard: {key + '*'}. Exiting.")
            paper_path = paper_path_li[0]
                
        LOGGER.info(f"Found paper: {paper_path}: Removing it and updating database.")
        shutil.rmtree(paper_path)
        self.remove_from_db(column="bibtex_path", value=str(paper_path / BIBTEX_NAME))
        self._update_db()

    def _update_db(self):
        # Write out bibliography file
        LOGGER.info(f"Writing bibliography file to '{BIB_REF}'.")
        with open(BIB_REF, "w") as f:
            for paper_bibtex in self.db["bibtex_path"]:
                f.write(open(paper_bibtex, "r").read() + "\n")


@APP.command()
def doi(doi: str, key: str = None, pdf: str = None):
    """Gets the paper from an Arxiv reference string"""
    typer.echo(f"Adding new paper from {doi=}")
    refman = RefMan()
    new_citation = refman.add_using_doi(doi=doi, key=key, pdf=pdf)
    pyperclip.copy(f"\cite{{{new_citation}}}")


@APP.command()
def arxiv(arxiv: str, key: str = None):
    """Tries to find and download the paper using the DOI."""
    typer.echo(f"Adding new paper from {arxiv=}")
    refman = RefMan()
    new_citation = refman.add_using_arxiv(arxiv=arxiv, key=key)
    pyperclip.copy(f"\cite{{{new_citation}}}")


@APP.command()
def bibtex(bibtex: str, key: str = None, pdf: str = None):
    """Adds an entry to the database from a bibtex-string."""
    typer.echo(f"Adding new paper from bibtex.")
    refman = RefMan()
    new_citation = refman.add_using_bibtex(bibtex_str=bibtex, key=key, pdf_path=pdf)
    pyperclip.copy(f"\cite{{{new_citation}}}")


@APP.command()
def rekey(key: str, new_key: str):
    """Modify the key of a paper."""
    refman = RefMan()
    new_citation = refman.rekey(key=key, new_key=new_key)
    pyperclip.copy(f"\cite{{{new_citation}}}")


@APP.command()
def rm(key: str):
    """Removes a paper from the disk and database."""
    typer.echo(f"Attempting to remove paper with key:")
    refman = RefMan()
    new_citation = refman.remove_paper(key=key)


if __name__ == "__main__":
    APP()
