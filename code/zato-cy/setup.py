# -*- coding: utf-8 -*-

"""
Copyright (C) 2017, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function

# flake8: noqa
from setuptools import Extension, find_packages, setup
from Cython.Build import cythonize

setup(
      name = 'zato-cy',
      version = '3.0.0+src',

      author = 'Zato Developers',
      author_email = 'info@zato.io',
      url = 'https://zato.io',

      package_dir = {'':'src'},
      packages = find_packages('src'),

      namespace_packages = ['zato'],
      ext_modules = cythonize([
          Extension(name='zato.bunch', sources=['src/zato/cy/bunch.pyx']),
          Extension(name='zato.url_dispatcher', sources=['src/zato/cy/url_dispatcher.pyx']),
        ]),

      zip_safe = False,
)
