# -*- coding: utf-8 -*-

'''

  abstract adapter tests
  ~~~~~~~~~~~~~~~~~~~~~~

  tests abstract adapter classes, that enforce/expose
  interfaces known to the model engine proper.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# canteen test
from canteen.test import FrameworkTest

# canteen model API
from canteen import model
from canteen.model.adapter import abstract


## AbstractModelAdapterTests
# Tests the `AbstractModelAdapter` class.
class AbstractModelAdapterTests(FrameworkTest):

  ''' Tests `model.adapter.abstract.ModelAdapter` '''

  __abstract__ = True
  subject = abstract.ModelAdapter

  def test_abstract(self):

    ''' Test `ModelAdapter` interface abstractness '''

    if getattr(self, '__abstract__', False):
      with self.assertRaises(TypeError):
        self.subject()
    else:
      self.subject()

  def test_utilities(self):

    ''' Test `ModelAdapter` internal utilities '''

    assert hasattr(self.subject, 'acquire')

    assert hasattr(self.subject, 'config')
    assert hasattr(self.subject, 'logging')
    assert hasattr(self.subject, 'serializer')
    assert hasattr(self.subject, 'encoder')
    assert hasattr(self.subject, 'compressor')

  def test_base_interface_compliance(self):

    ''' Test base `ModelAdapter` interface compliance '''

    assert hasattr(self.subject, 'get')
    assert hasattr(self.subject, 'put')
    assert hasattr(self.subject, 'delete')
    assert hasattr(self.subject, 'allocate_ids')
    assert hasattr(self.subject, 'encode_key')


## IndexedModelAdapterTests
# Tests the `IndexedModelAdapterAdapter` class.
class IndexedModelAdapterTests(AbstractModelAdapterTests):

  ''' Tests `model.adapter.abstract.IndexedModelAdapter` '''

  __abstract__ = True
  subject = abstract.IndexedModelAdapter

  def test_indexed_interface_compliance(self):

    ''' Test `IndexedModelAdapter` interface compliance '''

    assert hasattr(self.subject, 'write_indexes')
    assert hasattr(self.subject, 'clean_indexes')
    assert hasattr(self.subject, 'execute_query')


## GraphModelAdapterTests
# Tests the `GraphModelAdapterAdapter` class.
class GraphModelAdapterTests(IndexedModelAdapterTests):

  ''' Tests `model.adapter.abstract.GraphModelAdapter` '''

  __abstract__ = True
  subject = abstract.GraphModelAdapter

  def test_graph_interface_compliance(self):

    ''' Test `GraphModelAdapter` interface compliance '''

    assert hasattr(self.subject, 'edges')
    assert hasattr(self.subject, 'connect')
    assert hasattr(self.subject, 'neighbors')
