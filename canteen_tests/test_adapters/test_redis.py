# -*- coding: utf-8 -*-

'''

  redis adapter tests
  ~~~~~~~~~~~~~~~~~~~

  tests canteen's redis adapter.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# abstract test bases
from .test_abstract import IndexedModelAdapterTests


## RedisAdapterTests
# Tests the `Redis` model adapter.
class RedisAdapterTests(IndexedModelAdapterTests):

  ''' Tests `model.adapter.redis.Redis` '''
