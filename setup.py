#!/usr/bin/env python
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Get the version from the relevant file
with open(path.join(here, 'version'), encoding='utf-8') as f:
    version = f.read().strip()

setup(
    name='manuallabour',
    version=version,
    packages=find_packages("src"),
    package_dir={"" : "src"},
    namespace_packages=[
        'manuallabour',
        'manuallabour.exporters',
        'manuallabour.layouts',
        'manuallabour.layouts.html_single'],
    description='Library for processing step by step instructions',
    long_description=long_description,
    install_requires = ['jsonschema','jinja2'],
    package_data = {
        'manuallabour.core' : ['schema/*.json'],
        'manuallabour.exporters' : ['schema/*.json'],
        'manuallabour.layouts.html_single.basic' : ['template']
    },
    extras_require = {
        'graph': ['pygraphviz'],
        'pylint': ['pylint']
    },
    author="Johannes Reinhardt",
    author_email="jreinhardt@ist-dein-freund.de",
    license="LGPL 2.1+",
    keywords="step-by-step instructions"
)
