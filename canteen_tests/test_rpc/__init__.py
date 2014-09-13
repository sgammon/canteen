# -*- coding: utf-8 -*-

"""

  RPC tests
  ~~~~~~~~~

  tests canteen's server-side RPC layer.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

if __debug__:

  # RPC tests
  from . import test_base
  from . import test_exceptions

  # protocol tests
  from . import test_json
  from . import test_msgpack


  __all__ = ('test_base',
             'test_exceptions',
             'test_json',
             'test_msgpack')
