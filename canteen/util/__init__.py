# -*- coding: utf-8 -*-

'''

  canteen util
  ~~~~~~~~~~~~

  low-level utilities and miscellaneous tools that don't really
  belong anywhere special.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import pkgutil
import importlib


def walk(root=None):

  '''  '''

  return map(lambda (loader, name, is_package): importlib.import_module(name).__name__ if not is_package
    else name, pkgutil.walk_packages(root or '.'))
