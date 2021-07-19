import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="refman",
    version="0.0.2",
    description="RefMan - A Simple python-based reference manager",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/adriancaruana/refman",
    author="Adrian Caruana",
    author_email="adrian@adriancaruana.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    packages=["refman"],
    keywords=["Reference", "Manager", "BibTeX", "crossref"],
    include_package_data=True,
    zip_safe=False,
    # data_files=[("refman/templates", ["refman/templates/index.html"])],
    install_requires=[
        "arxiv2bib",
        "bibtexparser",
        "bs4",
        "flask",
        "numpy",
        "pandas",
        "pyperclip",
        "retrying",
        "tqdm",
        "typer",
    ],
    entry_points={
        "console_scripts": [
            "refman=refman.refman:APP",
        ]
    },
)
