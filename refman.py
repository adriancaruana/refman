#!/bin/python
# This scrit:
# (1) Reads doi.txt, a csv of reference data
# (2) For each reference (row) check that the PDF exists in `papers`
#
# optional arguments:
#   -a (DOI|PMID|URL), --append (DOI|PMID|URL)


import scihub
import pandas as pd
import dataclasses
from pathlib import Path

ROOTDIR = Path(__file__).parent.absolute()
PAPER_DIR = ROOTDIR / "papers"
BIB_DB = ROOTDIR / "ref.csv"
BIB_REF = ROOTDIR / "ref.bib"
COLUMNS = [
    "author",
    "doi",
    "issn",
    "journal",
    "month",
    "number",
    "pages",
    "publisher",
    "title",
    "url",
    "volume",
    "year",
    "filename"
]

@dataclasses.dataclass
class RefMan:
    append: str = dataclasses.field(default=None)
    db: pd.DataFrame = dataclasses.field(init=False, default=None)

    def parse_db(self):
        if not self.db:
            self.db = pd.read_csv(BIB_DB)
        return self.db
    
    def run():
        pass



def main():
    parser = argparse.ArgumentParser(description='RefMan - A Simple python-based reference manager.')
    parser.add_argument(
        '-a',
        '--append',
        metavar='(DOI|PMID|URL)',
        help='tries to find and download the paper',
        type=str,
        default=None
    )
    args = parser.parse_args()

    PAPER_DIR.mkdir(exist_ok=True)
    if not BIB_DB.exists() and args.append is None:
        raise FileNotFoundError(
            "Reference database 'ref.csv' not found. "
            "If this is your first time using refman.py, you can build an "
            "initial database using the `--append` argument."
        )

    refman = RefMan(append=args.append).run()


if __name__ == "__main__":
    main()
