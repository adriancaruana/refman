#!/bin/python
# RefMan - A Simple python-based reference manager.
# Author: Adrian Caruana
# optional arguments:
#   -a (DOI|PMID|URL), --append (DOI|PMID|URL)
#   -v , --verify
import os
import argparse
from scihub import SciHub
import pandas as pd
import dataclasses
from pathlib import Path
import requests
import logging

LOGGER = logging.getLogger(f"refman.{__name__}")
LOGGER.setLevel(logging.INFO)

ROOTDIR = Path(os.getenv("REFMAN_DATA", Path(__file__).parent / "refman_data")).absolute()
PAPER_DIR = ROOTDIR / "papers"
BIB_DB = ROOTDIR / "ref.csv"
BIB_REF = ROOTDIR / "ref.bib"
CROSSREF_URL = "http://api.crossref.org/works/{doi}/transform/application/{fmt}"
FMT_BIBTEX = "x-bibtex"
FMT_CITEPROC = "citeproc+json"

@dataclasses.dataclass
class RefMan:
    append: str = dataclasses.field(default=None)
    verify: bool = dataclasses.field(default=False)
    db: pd.DataFrame = dataclasses.field(init=False, default=None)

    def __post_init__(self):
        self.sh = SciHub()
        if not BIB_DB.exists() and self.append is None:
            raise FileNotFoundError(
                "Reference database 'ref.csv' not found. "
                "If this is your first time using refman.py, you can build an "
                "initial database using the `--append` argument."
            )
        if not BIB_DB.exists():
            LOGGER.info("Database doesn't exist, creating one.")
            self._init_db()
        else:
            LOGGER.info("Parsing database.")
            self._parse_db()

    def _init_db(self):
        self.db = pd.DataFrame(None)

    def _parse_db(self):
        if not self.db:
            self.db = pd.read_csv(BIB_DB)
        return self.db

    def _process_doi(self, doi: str):
        # Download and save the PDF using sci-hub
        if doi in self.db.get("DOI", list()):
            LOGGER.info(f"For {doi=}: Retrieving PDF.")
            return
        LOGGER.info(f"For {doi=}: Retrieving PDF.")
        metadata = self.sh.fetch(doi)
        with open(PAPER_DIR / metadata['name'], 'wb') as f:
            f.write(metadata['pdf'])
        # Fetch the reference data from cross-ref
        LOGGER.info(f"For {doi=}: Retrieving structured reference info.")
        r = dict(requests.get(CROSSREF_URL.format(doi=doi, fmt=FMT_CITEPROC)).json())
        LOGGER.info(f"For {doi=}: Retrieving bibtex entry.")
        r["bibtex"] = str(requests.get(CROSSREF_URL.format(doi=doi, fmt=FMT_BIBTEX)).content)
        r["filename"] = metadata['name']
        r["scihub_url"] = metadata['url']
        self.db = self.db.append(r, ignore_index=True)

    def _verify_db(self):
        LOGGER.info("Verifying PDF's in database.")
        for fname in self.db["filename"]:
            if not (PAPER_DIR / fname).exists():
                raise ValueError(f"Could not find {fname=} in {PAPER_DIR=}.")

    def _finish(self):
        # Write out the database
        LOGGER.info(f"Writing database to '{BIB_DB}' as csv.")
        self.db.to_csv(BIB_DB)
        # Write out bibliography file
        LOGGER.info(f"Writing bibliography file to '{BIB_DB}'.")
        with open(BIB_REF, 'w') as f:
            for ref in self.db["bibtex"]:
                f.write(eval(ref).decode("utf-8") + "\n")

    def run(self):
        if self.append is not None:
            for doi in self.append:
                self._process_doi(doi)

        if self.verify:
            self._verify_db()

        self._finish()

def main():
    parser = argparse.ArgumentParser(description='RefMan - A Simple python-based reference manager.')
    parser.add_argument(
        '-a',
        '--append',
        metavar='(DOI|PMID|URL)',
        help='Tries to find and download the paper. Append multiple papers using a space-separated list',
        type=str,
        nargs='+',
        default=None
    )
    parser.add_argument(
        '-v',
        '--verify',
        help=f'Verifies whether all entries in the database are present in {PAPER_DIR=}',
        action='store_true',
    )
    args = parser.parse_args()

    if not os.getenv("REFMAN_DATA", False):
        LOGGER.warning(f"`REFMAN_DATA` not found in environment variables. Using {ROOTDIR} as data path.")
    PAPER_DIR.mkdir(exist_ok=True, parents=True)

    refman = RefMan(append=args.append, verify=args.verify).run()


if __name__ == "__main__":
    main()