# -*- coding: utf-8 -*-

'''

  util tests
  ~~~~~~~~~~

  tests for canteen's most basic utilities.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os

if 'TEST_REIMPORT' in os.environ:  # pragma: nocover
  from canteen_tests.test_util import test_struct
  from canteen_tests.test_util import test_decorators
  from canteen_tests.test_util import test_debug
  from canteen_tests.test_util import test_config
  from canteen_tests.test_util import test_cli


__all__ = (
  'test_struct',
  'test_decorators',
  'test_debug',
  'test_config',
  'test_cli'
)
