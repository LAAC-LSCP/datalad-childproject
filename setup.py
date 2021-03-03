#!/usr/bin/env python

import sys
from setuptools import setup
import datalad_childrecords

from _datalad_buildsupport.setup import (
    BuildManPage,
)

cmdclass = {
    'build_manpage': BuildManPage
}

# Give setuptools a hint to complain if it's too old a version
# 30.3.0 allows us to put most metadata in setup.cfg
# Should match pyproject.toml
SETUP_REQUIRES = ['setuptools >= 30.3.0']
# This enables setuptools to install wheel on-the-fly
SETUP_REQUIRES += ['wheel'] if 'bdist_wheel' in sys.argv else []

if __name__ == '__main__':
    setup(name='datalad_childrecords',
          version=datalad_childrecords.__version__,
          cmdclass=cmdclass,
          setup_requires=SETUP_REQUIRES,
          entry_points={
              'datalad.metadata.extractors': [
                  'childrecords=datalad_childrecords.extractor:MetadataExtractor',
              ],
          },
    )

