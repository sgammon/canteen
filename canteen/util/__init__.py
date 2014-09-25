# -*- coding: utf-8 -*-

"""

  util
  ~~~~

  low-level utilities and miscellaneous tools that don't really
  belong anywhere special.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

from __future__ import print_function

# stdlib
import pkgutil

# submodules
from .cli import *
from .debug import *
from .config import *
from .struct import *
from .decorators import *


def say(*args):  # pragma: no cover

  """ Simply stringify and print the positional arguments received as ``args``.

      :param args: Positional arguments to ``repr`` and print.
      :returns: ``None``. """

  print(' '.join(map(lambda x: repr(x), args)))


def walk(root=None, debug=__debug__):  # pragma: no cover

  """ Force-walk all packages from ``root`` downward. DANGER: WILL IMPORT ALL
      MODULES BY FORCE, possibly loading code you didn't mean to load, or
      triggering scripts that aren't properly guarded against ``__main__``.

      :param root: Path to start walking packages from. Defaults to ``.``,
        meaning the current working directory.

      :param debug: ``bool`` debug flag - if ``True``, will print information
        about imported/found modules as it goes, and will raise exceptions
        instead of printing information about them.

      :returns: ``None``.  """

  # make sure working directory is in path
  if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

  def walker(bundle):  # pragma: no cover

    """ Inner function for recursively walking down a bundle. Print errors as
        they are encountered, raising them if ``debug`` is active.

        :param bundle: Current module bundle to work with, passed in from
          ``pkgutil.walk_packages`` in the form of ``loader``, ``name``, and
          ``is_package``.

        :returns: ``None``. """

    loader, name, is_package = bundle

    try:
      return importlib.import_module(name).__name__ if not is_package else name
    except ImportError as e:  # pragma: no cover
      print('Failed to preload path "%s"...' % (root or '.'))
      print(e)
      if debug: raise

  if debug: print('Preloading path "%s"...' % (root or '.'))
  say_lambda = (lambda x: say('Preloaded:', x) if x else None) if (
      debug) else (lambda x: x)
  map(say_lambda,
      map(walker, pkgutil.walk_packages(root or '.')))


__all__ = ('walk',
           'say',
           'cli',
           'config',
           'debug',
           'decorators',
           'struct',
           'bind')
