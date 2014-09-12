# -*- coding: utf-8 -*-

"""

  redis adapter tests
  ~~~~~~~~~~~~~~~~~~~

  tests canteen's redis adapter.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# abstract test bases
from canteen_tests.test_adapters import test_abstract

# redis adapter
from canteen.model.adapter import redis as rapi


try:
  import redis
except ImportError:  # pragma: no cover
  redis = None

try:
  import fakeredis
except ImportError:  # pragma: no cover
  fakeredis = None


if redis or fakeredis:


  class RedisAdapterTests(test_abstract.DirectedGraphAdapterTests):

    """ Tests `model.adapter.redis.Redis` in the default mode of operation,
        called ``toplevel_blob``. """

    # @TODO(sgammon): mock redis testing

    __abstract__ = False
    __original_mode__ = None
    subject = rapi.RedisAdapter
    mode = rapi.RedisMode.toplevel_blob

    def setUp(self):

      """ Set Redis into testing mode. """

      rapi.RedisAdapter.__testing__ = True
      self.__original_mode__ = rapi.RedisAdapter.EngineConfig.mode
      rapi.RedisAdapter.EngineConfig.mode = self.mode
      super(test_abstract.DirectedGraphAdapterTests, self).setUp()

    def tearDown(self):

      """ Set Redis back into non-testing mode. """

      rapi.RedisAdapter.__testing__ = False
      rapi.RedisAdapter.EngineConfig.mode = self.__original_mode__
      super(test_abstract.DirectedGraphAdapterTests, self).tearDown()


  class RedisAdapterHashKindBlobTests(RedisAdapterTests):

    """ Tests `model.adapter.redis.Redis` in ``hashkind_blob`` mode. """

    mode = rapi.RedisMode.hashkind_blob


  class RedisAdapterHashKeyBlobTests(RedisAdapterTests):

    """ Tests `model.adapter.redis.Redis` in ``hashkind_blob`` mode. """

    mode = rapi.RedisMode.hashkey_blob


  # @TODO(sgammon): add hashkey_hash testing when that mode is supported


else:  # pragma: no cover
  print("Warning! Redis not found, skipping Redis testsuite.")
