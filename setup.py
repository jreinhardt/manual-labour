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
    packages=find_packages(exclude=['tests','docs']),
    namespace_packages=['manuallabour'],
    description='Library for processing step by step instructions',
    long_description=long_description,
    install_requires = ['jsonschema'],
    extras_require = {
        'graph': ['pygraphviz']
    },
)
