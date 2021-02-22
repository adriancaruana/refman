import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="refman",
    version="0.0.1",
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
    install_requires=[
        "pandas",
        "bibtexparser",
        "bs4",
        "numpy",
        "retrying",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "refman=refman.refman:main",
        ]
    },
)
