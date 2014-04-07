# -*- coding: utf-8 -*-

'''

  canteen: util
  ~~~~~~~~~~~~~

  low-level utilities and miscellaneous tools that don't really
  belong anywhere special.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os
import sys
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


def walk(root=None, debug=__debug__):

  '''  '''

  # make sure working directory is in path
  if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

  def walker((loader, name, is_package)):

    '''  '''

    try:
      return importlib.import_module(name).__name__ if not is_package else name
    except ImportError as e:
      if debug:
        print 'Failed to preload path "%s"...' % (root or '.')
        print e
        raise
      return
    return (mod.__name__, is_package)

  if debug: print 'Preloading path "%s"...' % (root or '.')
  return map((lambda x: say('Preloaded:', x[0]) if x[0] else None) if debug else (lambda x: x),
          map(walker, pkgutil.walk_packages(root or '.')))


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
