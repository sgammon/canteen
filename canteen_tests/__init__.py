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
  from . import test_rpc
  from . import test_core
  from . import test_util
  from . import test_test
  from . import test_model
  from . import test__init__
  from . import test__main__
  from . import test_dispatch


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
