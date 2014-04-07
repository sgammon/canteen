# -*- coding: utf-8 -*-

'''

  canteen: core tests
  ~~~~~~~~~~~~~~~~~~~

  tests canteen's core, which contains abstract/meta code for constructing
  and gluing together the rest of canteen.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os

if 'TEST_REIMPORT' in os.environ:  # pragma: nocover
  from canteen_tests.test_core import test_runtime
  from canteen_tests.test_core import test_meta
  from canteen_tests.test_core import test_injection


__all__ = (
  'test_runtime',
  'test_injection',
  'test_meta'
)
