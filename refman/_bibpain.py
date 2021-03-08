#!/usr/bin/env python3
# Taken from:
# https://github.com/peterwittek/bibpain/blob/master/scripts/bibpain.py
import os
import re
import pyperclip
import requests
import sys
import time
import urllib
from utf8tobibtex import utf8_to_bibtex
from arxiv2bib import ATOM, arxiv2bib

ARXIV_CATEGORIES = [
    "astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th",
    "math-ph", "nlin", "nucl-ex", "nucl-th", "physics", "quant-ph", "math",
    "q-bio", "q-fin", "stat"
]


def check_categories(text):
    for category in ARXIV_CATEGORIES:
        if category in text:
            return category
    return None


def doi2bib(doi):
    url = 'https://doi.org/' + urllib.request.quote(doi)
    header = {
        'Accept': 'application/x-bibtex',
    }
    response = requests.get(url, headers=header)
    return response.text


def get_bibid_for_arxiv(reference):
    xml_list = reference.xml.findall(ATOM + 'author/' + ATOM + 'name')
    first_author = xml_list[0].text.split()[-1].lower()
    titleword = reference.title.split()[0].lower()
    return first_author + reference.year + titleword


def normalize(text_):
    text = utf8_to_bibtex(text_)
    text = text.replace("{{\\textbackslash}hspace{0.167em}}", "")
    text = text.replace('\t', '  ')
    text = re.sub('"\n', '}\n', text)
    text = re.sub('=\w+"', '= {', text)
    year = None
    year_line = re.findall("year[^\n]*", text)
    if year_line != []:
        year_string = year_line[0]
        if '{' not in year_string:
            year = year_string[-5:-1]
            text = text.replace(year_string,
                                year_string.replace(year, "{" + year + "}"))
        else:
            year = year_string[-6:-2]
    first_author = None
    author_line = re.findall("author[^\n]*", text)
    if author_line != []:
        author_list = author_line[0][author_line[0].find("{") + 1:-2]
        authors = author_list.split(" and ")
        if "," in authors[0]:
            first_author = authors[0][:authors[0].find(",")]
        else:
            first_author = authors[0][authors[0].rindex(" ") + 1:]
        first_author = first_author.lower()
    first_title_word = None
    title_line = re.findall("title[^\n]*", text)
    if title_line != []:
        first_title_word = re.findall("{[A-Za-z]*", title_line[0])[0][1:]
        first_title_word = first_title_word.lower()
    if first_title_word is not None and first_author is not None and \
            year is not None:
        original_id = text[text.find('{') + 1:text.find(',')]
        new_id = first_author + year + first_title_word
        text = text.replace(original_id, new_id)
    if "timestamp" not in text:
        timestamp = ",\n  timestamp={" + time.strftime("%Y.%m.%d") + "}\n}"
        text = text[:-2] + timestamp
    journal_line = re.findall("journal *=[^\n]*", text)
    if journal_line != []:
        if "arXiv" in journal_line[0]:
            text = text.replace(journal_line[0], "archiveprefix = {arXiv},")
            text = text.replace("https://arxiv.org/abs/", "")
    month_line = re.findall(" *month *=[^\n]*\n", text)
    if month_line != []:
        text = text.replace(month_line[0], "")
    return text


def find_file(name):
    base_dir = os.getcwd()
    for root, dirs, files in os.walk(base_dir):
        if name in files:
            filename = os.path.join(root, name)
            return "	file = {" + filename[len(base_dir) + 1:] + "},"


def postprocess_arxiv(entry):
    id_ = entry.id
    url = entry.url.replace("http", "https")
    if id_[-2] == 'v':
        id_ = id_[:-2]
        url = url[:-2]
    if len(entry.doi) == 0:
        lines = ["@article{" + get_bibid_for_arxiv(entry)]
        for k, v in [("  author", " and ".join(entry.authors)), ("  title",
                                                                 entry.title),
                     ("  archiveprefix",
                      "arXiv"), ("  eprint", id_), ("  year", entry.year),
                     ("  note", entry.note), ("  abstract", entry.summary)]:
            if len(v):
                lines.append("%-13s = {%s}" % (k, v))
        return ("," + os.linesep).join(lines) + os.linesep + "}"
    else:
        result = doi2bib(entry.doi)[:-2]
        result += "," + os.linesep + "  archiveprefix = {arXiv}"
        result += "," + os.linesep + "%-13s = {%s}" % ("  eprint", id_)
        result += "," + os.linesep + "%-13s = {%s}" % ("  abstract",
                                                       entry.summary)
        return result + os.linesep + "}"


def process_id(id_):
    processed_id = id_.strip()
    if processed_id.endswith(",") or processed_id.endswith("}"):
        processed_id = processed_id[:-1]
    id_lower = processed_id.lower()
    category = check_categories(processed_id)
    if "iv:" in id_lower:
        processed_id = id_lower[id_lower.index(":") + 1:]
    elif "iv.org" in id_lower:
        if category is not None:
            processed_id = id_lower[id_lower.index(category):]
        else:
            processed_id = id_lower[id_lower.rindex("/") + 1:]
    elif "doi.org" in id_lower:
        processed_id = processed_id[id_lower.index("doi.org/") + 8:]
    regexp = re.compile(r'[a-zA-Z]+[0-9]+[a-zA-Z]+')
    if regexp.search(processed_id):
        return find_file(processed_id + ".pdf")
    elif category is not None and processed_id.startswith(category):
        bibtex = postprocess_arxiv(arxiv2bib([processed_id])[0])
    elif "/" in processed_id:
        bibtex = doi2bib(processed_id)
    else:
        bibtex = postprocess_arxiv(arxiv2bib([processed_id])[0])
    return normalize(bibtex)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(process_id(pyperclip.paste()))
    else:
        print(process_id(sys.argv[1]))
