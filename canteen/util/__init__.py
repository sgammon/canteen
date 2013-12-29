# -*- coding: utf-8 -*-

'''

  canteen util
  ~~~~~~~~~~~~

  low-level utilities and miscellaneous tools that don't really
  belong anywhere special.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import time
import pkgutil
import datetime
import importlib

# submodules
from .cli import *
from .debug import *
from .config import *
from .struct import *
from .decorators import *


def say(*args):

  '''  '''

  print ' '.join(map(lambda x: str(x), args))


def walk(root=None, debug=True):

  '''  '''

  if debug: print 'Preloading path "%s"...' % (root or '.')
  return map((lambda x: say('Preloaded:', x)) if debug else (lambda x: x),
          map(lambda (loader, name, is_package): importlib.import_module(name).__name__ if not is_package
            else name, pkgutil.walk_packages(root or '.')))


__all__ = (
  'walk',
  'say',
  'cli',
  'config',
  'debug',
  'decorators',
  'struct',
  'configured',
  'bind',
  'cacheable'
)
