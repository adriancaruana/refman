from pathlib import Path
import os


EDITOR = os.getenv("EDITOR", "nano")
REFMAN_DIR = Path(
    os.getenv("REFMAN_DATA", Path(os.getcwd()) / "refman_data")
).absolute()
PAPER_DIR = REFMAN_DIR / "papers"
BIB_DB = REFMAN_DIR / "references.csv"
BIB_REF = REFMAN_DIR / "ref.bib"
META_NAME = "meta.json"
BIBTEX_NAME = ".bib"
NOTES_NAME = "notes.org"
CROSSREF_URL = "http://api.crossref.org/works/{doi}/transform/application/{fmt}"
ARXIV_BIBTEX_URL = "https://arxiv.org/bibtex/{arxiv}"
ARXIV_PDF_URL = "https://arxiv.org/pdf/{arxiv}.pdf"
FMT_BIBTEX = "x-bibtex"
FMT_CITEPROC = "citeproc+json"
