import sys
from setuptools import setup, find_packages

package = "pycorenlp"
name = "py-stanford-corenlp"
version = "4.0.0"
description = "A Stanford Core NLP wrapper (UW-Macrostrat fork)"
license="GPLv2+"

author = "John J Czaplewski"
author_email = "jczaplew@gmail.com"
url = "https://github.com/UW-Macrostrat/py-stanford-corenlp"

install_requires = ["beautifulsoup4 >= 4.4.0", "pexpect >= 3.3", "unidecode >= 0.04.18"]


setup(
    name=name,
    version=version,
    description=description,
    author=author,
    author_email=author_email,
	license=license,
    url=url,
    packages=find_packages(),
    package_data = {"": ["*.properties"],
        "py-corenlp": ["*.properties"]},
    install_requires=install_requires,
    classifiers=[
        ("License :: OSI Approved :: GNU General Public License v2 or later "
            "(GPLv2+)"),
        "Programming Language :: Python :: 2.7",
    ],
)
