from pathlib import Path

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


DOI = "10.1146/annurev-statistics-031017-100045"
DOI_RESPONSES = {
    CROSSREF_URL.format(
        doi=DOI, fmt=FMT_CITEPROC
    ): b'{"indexed":{"date-parts":[[2021,5,14]],"date-time":"2021-05-14T07:47:03Z","timestamp":1620978423643},"reference-count":139,"publisher":"Annual Reviews","issue":"1","content-domain":{"domain":[],"crossmark-restriction":false},"published-print":{"date-parts":[[2018,3,7]]},"DOI":"10.1146\\/annurev-statistics-031017-100045","type":"article-journal","created":{"date-parts":[[2017,12,14]],"date-time":"2017-12-14T00:09:23Z","timestamp":1513210163000},"page":"501-532","source":"Crossref","is-referenced-by-count":93,"title":"Topological Data Analysis","prefix":"10.1146","volume":"5","author":[{"given":"Larry","family":"Wasserman","sequence":"first","affiliation":[{"name":"Department of Statistics and Data Science, Carnegie Mellon University, Pittsburgh, Pennsylvania 15217, USA;"}]}],"member":"22","container-title":"Annual Review of Statistics and Its Application","original-title":[],"language":"en","link":[{"URL":"http:\\/\\/www.annualreviews.org\\/doi\\/pdf\\/10.1146\\/annurev-statistics-031017-100045","content-type":"unspecified","content-version":"vor","intended-application":"similarity-checking"}],"deposited":{"date-parts":[[2019,10,8]],"date-time":"2019-10-08T00:22:44Z","timestamp":1570494164000},"score":1.0,"subtitle":[],"short-title":[],"issued":{"date-parts":[[2018,3,7]]},"references-count":139,"journal-issue":{"published-print":{"date-parts":[[2018,3,7]]},"issue":"1"},"alternative-id":["10.1146\\/annurev-statistics-031017-100045"],"URL":"http:\\/\\/dx.doi.org\\/10.1146\\/annurev-statistics-031017-100045","relation":{},"ISSN":["2326-8298","2326-831X"],"subject":["Statistics, Probability and Uncertainty","Statistics and Probability"],"container-title-short":"Annu. Rev. Stat. Appl."}',
    CROSSREF_URL.format(
        doi=DOI, fmt=FMT_BIBTEX
    ): b"@article{Wasserman_2018,\n\tdoi = {10.1146/annurev-statistics-031017-100045},\n\turl = {https://doi.org/10.1146%2Fannurev-statistics-031017-100045},\n\tyear = 2018,\n\tmonth = {mar},\n\tpublisher = {Annual Reviews},\n\tvolume = {5},\n\tnumber = {1},\n\tpages = {501--532},\n\tauthor = {Larry Wasserman},\n\ttitle = {Topological Data Analysis},\n\tjournal = {Annual Review of Statistics and Its Application}\n}",
}


ARXIV = "2104.13478"
ARXIV_RESPONSES = {
    ARXIV_BIBTEX_URL.format(
        arxiv=ARXIV
    ): b"@misc{bronstein2021geometric,\n      title={Geometric Deep Learning: Grids, Groups, Graphs, Geodesics, and Gauges}, \n      author={Michael M. Bronstein and Joan Bruna and Taco Cohen and Petar Veli\xc4\x8dkovi\xc4\x87},\n      year={2021},\n      eprint={2104.13478},\n      archivePrefix={arXiv},\n      primaryClass={cs.LG}\n}",
    ARXIV_PDF_URL.format(arxiv=ARXIV): open(
        str(Path(__file__).parent / "test.pdf"), "rb"
    ).read(),
}

BIBTEX = """
@article{Wasserman_2018,
	doi = {10.1146/annurev-statistics-031017-100045},
	url = {https://doi.org/10.1146%2Fannurev-statistics-031017-100045},
	year = 2018,
	month = {mar},
	publisher = {Annual Reviews},
	volume = {5},
	number = {1},
	pages = {501--532},
	author = {Larry Wasserman},
	title = {Topological Data Analysis},
	journal = {Annual Review of Statistics and Its Application}
}
"""
