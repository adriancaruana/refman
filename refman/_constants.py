from pathlib import Path
import os


REFMAN_DIR = Path(
    os.getenv("REFMAN_DATA", Path(os.getcwd()) / "refman_data")
).absolute()
PAPER_DIR = REFMAN_DIR / "papers"
BIB_DB = REFMAN_DIR / "references.csv"
BIB_REF = REFMAN_DIR / "ref.bib"
CROSSREF_URL = "http://api.crossref.org/works/{doi}/transform/application/{fmt}"
FMT_BIBTEX = "x-bibtex"
FMT_CITEPROC = "citeproc+json"
