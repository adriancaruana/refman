import hashlib
import os
import re
import requests
from functools import reduce

import bibtexparser


MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]
url_regex = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

doi_regex = r"\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\"&\'<>])\S)+)\b"


def md5_hexdigest(x: str):
    return hashlib.md5(x.encode("utf-8")).hexdigest()


def is_valid_url(url: str):
    return re.match(url_regex, url) is not None


def is_valid_doi(doi: str):
    return bool(re.match(doi_regex, doi))


def ua_requester_get(*args, **kwargs):
    """This is so that the APIs get duped into thinking that this script is a browser."""
    ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    if "headers" not in kwargs:
        kwargs["headers"] = {"User-Agent": ua}
    return requests.get(*args, **kwargs)


def fmt_arxiv_bibtex(arxiv_bib_str: str):
    """Ensure consistent formatting of arxiv bibtex files"""
    # My preferred format for ID is: 'FirstSurname_Year'
    b = bibtexparser.loads(arxiv_bib_str).entries[0]
    authors = b['author'].split(" and ")
    first_author_surname = authors[0].split(" ")[-1]
    id_fmt = f"{first_author_surname}_{b['year']}"

    lines = ["@article{" + id_fmt]
    for k, v in [
        ("Author", b['author']),
        ("Title", b['title']),
        ("Eprint", b['eprint']),
        ("DOI", b.get('doi', "")),
        ("Journal", f"arXiv preprint"),
        # ("Journal", (f"arXiv preprint {ref.category}")),
        ("ArchivePrefix", "arXiv"),
        ("PrimaryClass", b['primaryclass']),
        ("Year", b['year']),
        ("Month", MONTHS[int(b['eprint'][2:4]) - 1]),
        ("Url", f"https://arxiv.org/abs/{b['eprint']}"),
        ("File", id_fmt + ".pdf"),
    ]:
        if len(v):
            lines.append("    %-13s = {%s}" % (k, v))

    return ("," + os.linesep).join(lines) + os.linesep + "}"


def fix_month(bib_str: str) -> str:
    """Fixes the string formatting in a bibtex entry"""
    return (
        bib_str
        .replace("{Jan}", "jan").replace("{jan}", "jan")
        .replace("{Feb}", "feb").replace("{feb}", "feb")
        .replace("{Mar}", "mar").replace("{mar}", "mar")
        .replace("{Apr}", "apr").replace("{apr}", "apr")
        .replace("{May}", "may").replace("{may}", "may")
        .replace("{Jun}", "jun").replace("{jun}", "jun")
        .replace("{Jul}", "jul").replace("{jul}", "jul")
        .replace("{Aug}", "aug").replace("{aug}", "aug")
        .replace("{Sep}", "sep").replace("{sep}", "sep")
        .replace("{Oct}", "oct").replace("{oct}", "oct")
        .replace("{Nov}", "nov").replace("{nov}", "nov")
        .replace("{Dec}", "dec").replace("{dec}", "dec")
    )


def _compose(f, g):
    return lambda *a, **kw: f(g(*a, **kw))

def compose(*fs):
    return lambda x: reduce(lambda acc, f: f(acc), reversed(fs), x)

def fix_bibtex(bibtex: str):
    fn = compose(
        fix_month,
    )
    return fn(bibtex)
    


