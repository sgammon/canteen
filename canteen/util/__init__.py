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


def crawl(location=os.environ.get('CANTEEN_CONFIG', None)):

  '''  '''

  ## @TODO(sgammon): fix the shit out of this
  ## @TODO(sgammon): seriously fix it this is fucking gross

  if not location:  # if we aren't handed config...

    # try config at default path, otherwise defer
    try:
      import config
      return config
    except ImportError as e:
      pass

  else:
    if isinstance(location, basestring):  # it's probably an import path
      return importlib.import_module(location)

    if isinstance(location, type(os)):  # it's probably a config module
      return location.config  # should be mounted at ``config``
  return {}


def say(*args):

  '''  '''

  print ' '.join(map(lambda x: str(x), args))


def walk(root=None, debug=__debug__):

  '''  '''

  from canteen.core import meta

  # make sure working directory is in path
  if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

  def walker((loader, name, is_package)):

    '''  '''

    if name is '__main__' or '__main__' in name: return  # don't import __main__ builtins
    try:
      mod = meta.Loader.load(name)
      if mod == False:
        # module refused - canteen shouldn't load it
        mod = importlib.import_module(name)
      return None
    except ImportError as e:
      if debug:
        #print 'Failed to preload path "%s"...' % (root or '.')
        #print e
        pass
      return
    return mod.__name__

  if debug: print 'Preloading path "%s"...' % (root or '.')
  return map((lambda x: say('Preloaded:', x) if x else None) if debug else (lambda x: x),
          map(walker, pkgutil.walk_packages(root or '.')))


__all__ = (
  'crawl',
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
