import os
import sys
from pathlib import Path
import hashlib
import pytest
import shutil
import subprocess
import signal

import responses
import pyperclip

REFMAN_DATA = Path(__file__).parent / "TEST_REFMAN_DATA"
os.environ["REFMAN_DATA"] = str(REFMAN_DATA)
sys.path.append(str((Path(__file__).parent / "../").resolve().absolute()))

from refman._constants import (
    EDITOR,
    REFMAN_DIR,
    PAPER_DIR,
    BIB_DB,
    BIB_REF,
    META_NAME,
    BIBTEX_NAME,
    CROSSREF_URL,
    ARXIV_BIBTEX_URL,
    ARXIV_PDF_URL,
    FMT_BIBTEX,
    FMT_CITEPROC,
)
from refman.refman import doi, arxiv, bibtex, rekey, medit, rm

from _responses import DOI, DOI_RESPONSES, ARXIV, ARXIV_RESPONSES, BIBTEX


def clean_refman_data():
    if REFMAN_DATA.exists():
        shutil.rmtree(REFMAN_DATA)


@pytest.fixture(autouse=True)
def start_end():
    # Will be executed before the first test
    clean_refman_data()
    yield
    # Will be executed after the last test
    clean_refman_data()


class TestDoi:
    @responses.activate
    def test_doi(self):
        for k, v in DOI_RESPONSES.items():
            responses.add(responses.GET, k, v, status=200)
        doi(doi=DOI, key=None, pdf=None)
        assert pyperclip.paste() == "\\cite{Wasserman_2018}"
        with pytest.raises(StopIteration):
            # There should not be any PDF files
            next(REFMAN_DATA.rglob("*.pdf"))
        with pytest.raises(ValueError):
            doi(doi="0")
        with pytest.raises(ValueError):
            doi(doi="abcd")
        with pytest.raises(ValueError):
            doi(doi="")

    @responses.activate
    def test_doi_with_key(self):
        for k, v in DOI_RESPONSES.items():
            responses.add(responses.GET, k, v, status=200)
        doi(doi=DOI, key="TestKey_2000", pdf=None)
        assert pyperclip.paste() == "\\cite{TestKey_2000}"

    @responses.activate
    def test_doi_with_pdf(self):
        for k, v in DOI_RESPONSES.items():
            responses.add(responses.GET, k, v, status=200)
        pdf = Path(__file__).parent / "test.pdf"
        assert pdf.exists()
        doi(doi=DOI, key=None, pdf=str(pdf))
        assert pyperclip.paste() == "\\cite{Wasserman_2018}"
        ref = hashlib.md5(
            open(Path(__file__).parent / "test.pdf", "rb").read()
        ).hexdigest()
        src = hashlib.md5(
            open(next(REFMAN_DATA.rglob("*.pdf")), "rb").read()
        ).hexdigest()
        assert ref == src


class TestArxiv:
    @responses.activate
    def test_arxiv(self):
        for k, v in ARXIV_RESPONSES.items():
            responses.add(responses.GET, k, v, status=200)
        arxiv(arxiv=ARXIV, key=None)
        assert pyperclip.paste() == "\\cite{Bronstein_2021}"
        ref = hashlib.md5(
            open(Path(__file__).parent / "test.pdf", "rb").read()
        ).hexdigest()
        src = hashlib.md5(
            open(next(REFMAN_DATA.rglob("*.pdf")), "rb").read()
        ).hexdigest()
        assert ref == src
        with pytest.raises(ValueError):
            arxiv(arxiv=None, key=None)
        with pytest.raises(ValueError):
            arxiv(arxiv="", key=None)
        with pytest.raises(ValueError):
            arxiv(arxiv="abcd.1234", key=None)

    @responses.activate
    def test_arxiv_with_key(self):
        for k, v in ARXIV_RESPONSES.items():
            responses.add(responses.GET, k, v, status=200)
        arxiv(arxiv=ARXIV, key="TestKey_2001")
        assert pyperclip.paste() == "\\cite{TestKey_2001}"
        ref = hashlib.md5(
            open(Path(__file__).parent / "test.pdf", "rb").read()
        ).hexdigest()
        src = hashlib.md5(
            open(next(REFMAN_DATA.rglob("*.pdf")), "rb").read()
        ).hexdigest()
        assert ref == src


class TestBibtex:
    def test_bibtex(self):
        bibtex(bibtex=BIBTEX, key=None, pdf=None)
        assert pyperclip.paste() == "\\cite{Wasserman_2018}"
        with pytest.raises(StopIteration):
            # There should not be any PDF files
            next(REFMAN_DATA.rglob("*.pdf"))

    def test_bibtex_with_key(self):
        bibtex(bibtex=BIBTEX, key="TestKey_2002", pdf=None)
        assert pyperclip.paste() == "\\cite{TestKey_2002}"
        with pytest.raises(StopIteration):
            # There should not be any PDF files
            next(REFMAN_DATA.rglob("*.pdf"))

    def test_bibtex_with_pdf(self):
        pdf = Path(__file__).parent / "test.pdf"
        assert pdf.exists()
        bibtex(bibtex=BIBTEX, key=None, pdf=pdf)
        assert pyperclip.paste() == "\\cite{Wasserman_2018}"
        ref = hashlib.md5(
            open(Path(__file__).parent / "test.pdf", "rb").read()
        ).hexdigest()
        src = hashlib.md5(
            open(next(REFMAN_DATA.rglob("*.pdf")), "rb").read()
        ).hexdigest()
        assert ref == src


class TestRekey:
    def test_rekey(self):
        bibtex(bibtex=BIBTEX, key=None, pdf=None)
        assert pyperclip.paste() == "\\cite{Wasserman_2018}"
        rekey("Wass", "Rekey_2003")  # Use the wildcard by default
        assert pyperclip.paste() == "\\cite{Rekey_2003}"


class TestRm:
    def test_rm(self):
        bibtex(bibtex=BIBTEX, key=None, pdf=None)
        assert pyperclip.paste() == "\\cite{Wasserman_2018}"
        assert len([f for f in REFMAN_DATA.iterdir() if f.is_dir()]) == 1
        rm("Wass")  # Use the wildcard by default
        assert len([f for f in REFMAN_DATA.iterdir() if f.is_dir()]) == 0


class TestMedit:
    def test_medit_noaction(self, monkeypatch):
        bibtex(bibtex=BIBTEX, key=None, pdf=None)

        def dummyfn(*a, **kw):
            return 0

        monkeypatch.setattr(subprocess, "call", dummyfn)
        medit("Wasser")

    def test_medit_edit(self, monkeypatch):
        bibtex(bibtex=BIBTEX, key=None, pdf=None)

        def dummyfn(*a, **kw):
            f = next(REFMAN_DATA.rglob("*/.bib"))
            old_bibtex = open(f, "r").read()
            new_bibtex = old_bibtex.replace("Wasserman_2018", "TestKey_2004")
            open(f, "w").write(new_bibtex)
            print(f, "\n", open(f, "r").read())
            return 0

        monkeypatch.setattr(subprocess, "call", dummyfn)
        medit("Wasser")
        assert pyperclip.paste() == "\\cite{TestKey_2004}"
