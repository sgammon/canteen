# -*- coding: utf-8 -*-

"""

  core runtime tests
  ~~~~~~~~~~~~~~~~~~

  tests canteen's runtime core, which is responsible for pulling
  the app together with glue and spit.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import operator

# testing
from canteen import test

# runtime core
from canteen.core import runtime


class BaseRuntimeTest(test.FrameworkTest):

  """ Tests :py:mod:`canteen`'s :py:mod:`core.runtime` package,
      which handles pretty much everything from bind to dispatch. """

  def test_exports(self):

    """ Test basic attributes that should always be present on `runtime` """

    assert hasattr(runtime, 'Runtime')
    assert hasattr(runtime, 'Library')


class RuntimeLibraryTest(test.FrameworkTest):

  """ Tests :py:class:`canteen.core.runtime.Library`, which is
      used internally by :py:mod:`canteen` for deferred library
      binding. """

  def test_good_library_string_lax(self):

    """ Test that `Library` can load a known-good module (by path) """

    with runtime.Library('operator') as (library, _operator):
      assert hasattr(_operator, 'eq')
      assert operator.eq is _operator.eq

  def test_good_library_string_strict(self):

    """ Test that `Library` can load a known-good module in `strict` mode """

    with runtime.Library('operator', strict=True) as (library, _operator):
      assert hasattr(_operator, 'eq')
      assert operator.eq is _operator.eq

  def test_bad_library_string_lax(self):

    """ Test that `Library` can ignore a known-bad module (by path) """

    _lib = runtime.Library('i_do_not_exist_at_all_okay_never')
    _lib.__enter__()

  def test_bad_library_string_strict(self):

    """ Test that `Library` can ignore a known-bad module in `strict` mode """

    with self.assertRaises(ImportError):
      _lib = runtime.Library('i_do_not_exist_at_all_okay_never', strict=True)
      _lib.__enter__()

  def test_good_library_module_lax(self):

    """ Test that `Library` can load a module (by mod) """

    with runtime.Library(operator) as (library, _operator):
      assert hasattr(_operator, 'eq')

  def test_good_library_module_strict(self):

    """ Test that `Library` can load a module (by mod) in `strict` mode """

    with runtime.Library(operator, strict=True) as (library, _operator):
      assert hasattr(_operator, 'eq')
