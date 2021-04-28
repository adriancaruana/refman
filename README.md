# RefMan
RefMan - A Simple python-based reference manager

## How `RefMan` works
`RefMan` capitalises on [Sci-hub](https://sci-hub.se/) and [crossref](https://crossref.org) to 
provide a very simple Python-based reference manager.

The goal of `RefMan` is to prioritise getting bibliographic data and PDFs, wihtout having to worry about databases or manually downloading and maintaining references yourself.

`RefMan` maintains:
 1. a BibTeX bibliography file `ref.bib`, and
 2. a directory of `pdf`'s in a `REFMAN_DATA`.

`RefMan`'s output is stored in `refman_data` in the current working directory, or sourced from a
path listed under the `REFMAN_DATA` environment variable.

## How to use `RefMan`

Adding new papers to `refman_data` can be achieved in three ways:
 1. With a DOI, using `-d, --doi`, or
 2. With an `arxiv` reference using `-a, --arxiv`, or
 3. As a last-resort, with a BibTeX string using `-b, --bibtex`, alongside an optional PDF (url or local-path) using `-p, --pdf`.

## Installing

```bash
git clone https://https://github.com/adriancaruana/refman
cd refman
./install
```

## Getting Started

```bash
# Make a directory to store references
mkdir ~/refman_data

# Set the REFMAN_DATA environment variable. Add this to your `.bashrc` for persistence.
export REFMAN_DATA=$HOME/refman_data

# Add a paper using a DOI:
refman -d 10.1103/PHYSREVLETT.116.061102

# Add a paper using an `arxiv` reference
refman -a 2103.16574

# Add a paper using a bibtex string & pdf.
refman -b "@inproceedings{devlin2018bert,
	title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
	author="Jacob {Devlin} and Ming-Wei {Chang} and Kenton {Lee} and Kristina N. {Toutanova}",
	booktitle="Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers)",
	pages="4171--4186",
	year="2018"
}" -p "https://www.aclweb.org/anthology/N19-1423.pdf"
```

## Usage

```
usage: refman [-h] [-d DOI] [-a ARXIV] [-b BIBTEX] [-p PDF] [-k KEY]

RefMan - A Simple python-based reference manager.

optional arguments:
  -h, --help            show this help message and exit
  -d DOI, --doi DOI     Tries to find and download the paper using the DOI.
  -a ARXIV, --arxiv ARXIV
                        Gets the paper from an Arxiv reference string.
  -b BIBTEX, --bibtex BIBTEX
                        Adds an entry to the database from a bibtex-string. Optionally, provide -p,
                        --pdf to associate this entry with a PDF.
  -p PDF, --pdf PDF     Adds an entry to the database from a bibtex-string. Optionally, provide -p,
                        --pdf to associate this entry with a PDF.
  -k KEY, --key KEY     Explicitly define the key to use (without hash) for the paper.
```