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
  import fakeredis
except ImportError:  # pragma: no cover
  fakeredis = None


if fakeredis:


  class RedisSetupTeardown(object):

    """ Packages Redis setup and teardown methods. """

    def test_adapter_mode(self):

      """ Test the adapter's internal mode against what we expect it to be """

      if not self.__abstract__:
        assert self.subject().__testing__ is True
        assert self.subject().EngineConfig.mode == self.mode


  class RedisAdapterTopLevelBlobTests(test_abstract.DirectedGraphAdapterTests,
                                      RedisSetupTeardown):

    """ Tests `model.adapter.redis.Redis` in ``toplevel_blob`` mode """

    __abstract__ = False
    subject = rapi.RedisAdapter
    mode = rapi.RedisMode.toplevel_blob

    @classmethod
    def setUpClass(cls):
      """ Set Redis into testing mode. """

      rapi._mock_redis = fakeredis.FakeStrictRedis()
      rapi._mock_redis.flushall()
      rapi.RedisAdapter.__testing__ = True
      rapi.RedisAdapter.EngineConfig.mode = rapi.RedisMode.toplevel_blob

    @classmethod
    def tearDownClass(cls):
      """ Set Redis back into non-testing mode. """

      rapi._mock_redis = fakeredis.FakeStrictRedis()
      rapi._mock_redis.flushall()
      rapi.RedisAdapter.__testing__ = False
      rapi.RedisAdapter.EngineConfig.mode = rapi.RedisMode.toplevel_blob


  class RedisAdapterHashKindBlobTests(test_abstract.DirectedGraphAdapterTests,
                                      RedisSetupTeardown):

    """ Tests `model.adapter.redis.Redis` in ``hashkind_blob`` mode """

    __abstract__ = False
    subject = rapi.RedisAdapter
    mode = rapi.RedisMode.hashkind_blob

    @classmethod
    def setUpClass(cls):
      """ Set Redis into testing mode. """

      rapi.RedisAdapter.__testing__ = True
      rapi.RedisAdapter.EngineConfig.mode = rapi.RedisMode.hashkind_blob

    @classmethod
    def tearDownClass(cls):
      """ Set Redis back into non-testing mode. """

      rapi.RedisAdapter.__testing__ = False
      rapi.RedisAdapter.EngineConfig.mode = rapi.RedisMode.toplevel_blob


  class RedisAdapterHashKeyBlobTests(test_abstract.DirectedGraphAdapterTests,
                                     RedisSetupTeardown):

    """ Tests `model.adapter.redis.Redis` in ``hashkey_blob`` mode """

    __abstract__ = False
    subject = rapi.RedisAdapter
    mode = rapi.RedisMode.hashkey_blob

    @classmethod
    def setUpClass(cls):
      """ Set Redis into testing mode. """

      rapi.RedisAdapter.__testing__ = True
      rapi.RedisAdapter.EngineConfig.mode = rapi.RedisMode.hashkey_blob

    @classmethod
    def tearDownClass(cls):
      """ Set Redis back into non-testing mode. """

      rapi.RedisAdapter.__testing__ = False
      rapi.RedisAdapter.EngineConfig.mode = rapi.RedisMode.toplevel_blob


  # @TODO(sgammon): add hashkey_hash testing when that mode is supported


else:  # pragma: no cover
  print("Warning! Redis not found, skipping Redis testsuite.")
