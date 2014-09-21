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

# redis adapter & model API
from canteen import model
from canteen.model.adapter import redis as rapi

# abstract test bases
from canteen_tests.test_adapters import test_abstract


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

    def test_put_entity(self):

      """ Test saving a basic entity to Redis with `RedisAdapter` """


      class SampleEntity(model.Model):

        """ quick sample entity """

        __adapter__ = rapi.RedisAdapter

        string = str, {'indexed': False}
        number = int, {'indexed': False}

      s = SampleEntity(key=model.Key(SampleEntity, 'sample'),
                       string='hi',
                       number=5)
      x = s.put(adapter=self.subject())

      assert s.string == 'hi'
      assert s.number == 5
      assert x.kind == 'SampleEntity'
      assert x.id == 'sample'

      return s, x, SampleEntity

    def test_delete_entity(self):

      """ Test deleting a basic entity from Redis with `RedisAdapter` """

      s, x, SampleEntity = self.test_put_entity()
      s.delete(adapter=self.subject())

      ss = SampleEntity.get(x, adapter=self.subject())
      assert not ss, "should have deleted entity but instead got '%s'" % ss


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
