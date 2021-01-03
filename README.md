# RefMan
RefMan - A Simple python-based reference manager

## How `RefMan` works
`RefMan` capitalises on [Sci-hub](https://sci-hub.se/) and [crossref](https://crossref.org) to 
provide a very simple Python-based reference manager.

`RefMan` maintains:
 1. a BibTeX bibliography file `ref.bib`, and
 2. a directory of `pdf`'s in a `REFMAN_DATA`.

`RefMan`'s output is stored in `refman_data` in the current working directory, or sourced from a
path listed under the `REFMAN_DATA` environment variable.

## How to use `RefMan`

Adding new papers to `refman_data` can be achieved in two ways:
 1. With a string-separated list of DOIs using `-d, --doi`, or
 2. With a BibTeX string using `-b, --bibtex`, alongside an optional PDF (url or local-path) using `-p, --pdf`.

```
usage: refman [-h] [-d DOI [DOI ...]] [-b BIBTEX] [-p PDF]

RefMan - A Simple python-based reference manager.

optional arguments:
  -h, --help            show this help message and exit
  -d DOI [DOI ...], --doi DOI [DOI ...]
                        Tries to find and download the paper using the DOI. Append multiple papers using a space-separated list
  -b BIBTEX, --bibtex BIBTEX
                        Adds an entry to the database from a bibtex-string. Optionally, provide -p, --pdf to associate this entry with a
                        PDF.
  -p PDF, --pdf PDF     Adds an entry to the database from a bibtex-string. Optionally, provide -p, --pdf to associate this entry with a
                        PDF.
```