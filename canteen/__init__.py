# -*- coding: utf-8 -*-

'''

  canteen
  ~~~~~~~

  a minimal web framework for the modern web

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# import ALL THE THINGS
import os, sys, pkgutil, importlib
map(lambda (loader, name, is_package): importlib.import_module(name).__name__ if not is_package else name, pkgutil.walk_packages('.'))
