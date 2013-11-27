# -*- coding: utf-8 -*-

'''

  canteen tests
  ~~~~~~~~~~~~~

  class structure and testsuite to put canteen functionality through
  unit/integration/functional-level testing.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''


if __debug__:

  # test tools
  from canteen import util
  from canteen import test

  # build the testsuite
  from .test_rpc import *
  from .test_core import *
  from .test_util import *
  from .test_test import *
  from .test_model import *
  from .test__init__ import *
  from .test__main__ import *
  from .test_dispatch import *


  class SanityTest(test.FrameworkTest):

    '''  '''

    def test_math_sanity(self):

      '''  '''

      self.assertEqual(1 + 1, 2)
      self.assertEqual(2 - 1, 1)

      assert (10 / 5) == 2
      assert (10 % 6) == 4

    def test_assert_sanity(self):

      '''  '''

      try:
        assert 1 == 2
      except AssertionError:
        pass
      else:
        raise RuntimeError('Assertions are disabled. Something is wrong, as `__debug__` is truthy.')
