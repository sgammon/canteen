# -*- coding: utf-8 -*-

'''

  canteen model adapter tests
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~

  tests canteen's model adapters.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
      A copy of this library is included as ``LICENSE.md`` in
      the root of the project.

'''

# stdlib
import os
import unittest

# canteen model API
from canteen import model

# canteen tests
from canteen.test import FrameworkTest


if 'TEST_REIMPORT' in os.environ:
  from canteen_tests.test_model.test_adapters import test_abstract
  from canteen_tests.test_model.test_adapters import test_core
  from canteen_tests.test_model.test_adapters import test_inmemory
  from canteen_tests.test_model.test_adapters import test_redis
  from canteen_tests.test_model.test_adapters import test_adapters
  from canteen_tests.test_model.test_adapters import test_exceptions


## AdapterExportTests
class AdapterExportTests(FrameworkTest):

  ''' Tests objects exported by `model.adapter`. '''

  @unittest.expectedFailure
  def test_top_level_adapter_exports(self):

    ''' Test that we can import concrete classes. '''

    try:
      from canteen import model
      from canteen.model import adapter

    except ImportError as e:  # pragma: no cover
      return self.fail("Failed to import model adapter package.")

    else:
      self.assertIsInstance(adapter, type(os))  # `adapter` module
      self.assertIsInstance(adapter.abstract, type(os))  # `adapter.abstract` export
      self.assertTrue(adapter.ModelAdapter)  # `ModelAdapter` parent class
      self.assertIsInstance(adapter.abstract_adapters, tuple)  # abstract adapter list
      self.assertTrue(adapter.IndexedModelAdapter)  # `IndexedModelAdapter` subclass
      self.assertIsInstance(adapter.sql, type(os))  # `sql` adapter
      self.assertIsInstance(adapter.redis, type(os))  # `redis` adapter
      self.assertIsInstance(adapter.mongo, type(os))  # `mongo` adapter
      self.assertIsInstance(adapter.protorpc, type(os))  # `protorpc` adapter
      self.assertIsInstance(adapter.pipeline, type(os))  # `pipeline` adapter
      self.assertIsInstance(adapter.memcache, type(os))  # `memcache` adapter
      self.assertIsInstance(adapter.inmemory, type(os))  # `inmemory` adapter
      self.assertIsInstance(adapter.modules, tuple)  # full modules tuple
      self.assertTrue(issubclass(adapter.SQLAdapter, adapter.ModelAdapter))  # SQL adapter
      self.assertTrue(issubclass(adapter.RedisAdapter, adapter.ModelAdapter))  # Redis adapter
      self.assertTrue(issubclass(adapter.MongoAdapter, adapter.ModelAdapter))  # Mongo adapter
      self.assertTrue(issubclass(adapter.MemcacheAdapter, adapter.ModelAdapter))  # Memcache adapter
      self.assertTrue(issubclass(adapter.InMemoryAdapter, adapter.ModelAdapter))  # InMemory adapter


## ModelAdapterTests
class ModelAdapterTests(FrameworkTest):

  ''' Test `adapter.abstract.ModelAdapter`. '''

  def test_adapter_registry(self):

    ''' Test `adapter.abstract.ModelAdapter.registry`. '''

    from canteen.model.adapter import abstract

    self.assertTrue(hasattr(abstract.ModelAdapter, 'registry'))
    self.assertIsInstance(abstract.ModelAdapter.registry, dict)

    ## SampleModel
    # Quick sample model to make sure class registration happens properly.
    class Sample(model.Model):

      ''' Quick sample model. '''

      pass

    # test that our class was registered
    self.assertTrue(('Sample' in abstract.ModelAdapter.registry))
    self.assertTrue(abstract.ModelAdapter.registry.get('Sample') == Sample)

  def test_default_adapter(self):

    ''' Test that the default adapter is assigned properly. '''

    from canteen.model import adapter
    from canteen.model.adapter import abstract

    ## TestDefault
    # Quick sample model to test default adapter injection.
    class TestDefault(model.Model):

      ''' Quick sample model. '''

      pass

    # test attribute + default injector
    self.assertTrue(hasattr(TestDefault, '__adapter__'))
    self.assertIsInstance(TestDefault.__adapter__, adapter.InMemoryAdapter)

  @unittest.expectedFailure
  def test_explicit_adapter(self):

    ''' Test that an adapter can be set explcitly. '''

    from canteen.model import adapter
    from canteen.model.adapter import abstract

    ## TestExplicit
    # Quick sample model to test explicit adapter injection.
    class TestExplicit(model.Model):

      ''' Quick sample model. '''

      __adapter__ = adapter.RedisAdapter

    # test attribute + explicit injector
    self.assertTrue(hasattr(TestExplicit, '__adapter__'))
    self.assertIsInstance(TestExplicit.__adapter__, adapter.RedisAdapter)
