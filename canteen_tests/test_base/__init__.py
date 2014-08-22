# -*- coding: utf-8 -*-

'''

  base tests
  ~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os

if 'TEST_REIMPORT' in os.environ:  # pragma: nocover
  from . import test_handler
  from . import test_logic
  from . import test_page
  from . import test_protocol


__all__ = (
  'test_handler',
  'test_logic',
  'test_page',
  'test_protocol'
)
