# RefMan
RefMan - A Simple python-based reference manager

## How `RefMan` works
`RefMan` capitalises on [Sci-hub](https://sci-hub.se/) and [crossref](https://crossref.org) to 
provide a very simple Python-based reference manager.

`RefMan` maintains:
 1. a database of references `ref.csv`,
 2. a BibTeX bibliography file `ref.bib`, and
 3. a directory of `pdf`'s in `papers/`.

`RefMan`'s output is stored in `refman_data` in the current working directory, or sourced from a
path listed under the `REFMAN_DATA` environment variable.

## How to use `RefMan`

There are two ways in which `RefMan` can be used:
 1. Adding new papers to the database. This is done using the `-a, --append` option.
 2. Looking up (printing) the important metadata (`pdf` filename, BibTeX key, Author, and Title) using the DOI of a paper which exists in the database. This is done using the `-l, --lookup` option.

References can be appended and looked-up at the same time.

```
usage: refman [-h] [-a (DOI|PMID|URL) [(DOI|PMID|URL) ...]] [-l LOOKUP] [-v]

RefMan - A Simple python-based reference manager.

optional arguments:
  -h, --help            show this help message and exit
  -a (DOI|PMID|URL) [(DOI|PMID|URL) ...], --append (DOI|PMID|URL) [(DOI|PMID|URL) ...]
                        Tries to find and download the paper. Append multiple papers using a space-separated list
  -l LOOKUP, --lookup LOOKUP
                        If it already exists in the database, return the filename of the pdf using it's DOI.
  -v, --verify          Verifies whether all entries in the database are present in PAPER_DIR=PosixPath('/home/adrian/phd/refman/refman_data/papers')
```