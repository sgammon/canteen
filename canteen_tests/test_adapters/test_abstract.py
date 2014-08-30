# -*- coding: utf-8 -*-

"""

  abstract adapter tests
  ~~~~~~~~~~~~~~~~~~~~~~

  tests abstract adapter classes, that enforce/expose
  interfaces known to the model engine proper.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import datetime

# canteen test
from canteen.test import FrameworkTest

# canteen model API
from canteen import model
from canteen.model.adapter import abstract


class AbstractModelAdapterTests(FrameworkTest):

  """ Tests `model.adapter.abstract.ModelAdapter` """

  __abstract__ = True
  subject = abstract.ModelAdapter

  def test_abstract(self):

    """ Test `ModelAdapter` interface abstractness """

    if getattr(self, '__abstract__', False):
      with self.assertRaises(TypeError):
        self.subject()
    else:  # pragma: no cover
      self.subject()

  def test_utilities(self):

    """ Test `ModelAdapter` internal utilities """

    assert hasattr(self.subject, 'acquire')
    assert hasattr(self.subject, 'config')
    assert hasattr(self.subject, 'logging')
    assert hasattr(self.subject, 'serializer')
    assert hasattr(self.subject, 'encoder')
    assert hasattr(self.subject, 'compressor')

  def test_base_interface_compliance(self):

    """ Test base `ModelAdapter` interface compliance """

    assert hasattr(self.subject, 'get')
    assert hasattr(self.subject, 'put')
    assert hasattr(self.subject, 'delete')
    assert hasattr(self.subject, 'allocate_ids')
    assert hasattr(self.subject, 'encode_key')


class IndexedModelAdapterTests(AbstractModelAdapterTests):

  """ Tests `model.adapter.abstract.IndexedModelAdapter` """

  __abstract__ = True
  subject = abstract.IndexedModelAdapter

  def test_indexed_interface_compliance(self):

    """ Test `IndexedModelAdapter` interface compliance """

    assert hasattr(self.subject, 'write_indexes')
    assert hasattr(self.subject, 'clean_indexes')
    assert hasattr(self.subject, 'execute_query')

  def test_attached_indexer_compliance(self):

    """ Test `IndexedModelAdapter.Indexer` for basic functionality """

    assert hasattr(self.subject, 'Indexer')
    indexer = self.subject.Indexer

    # interrogate indexer
    assert hasattr(indexer, 'convert_key')
    assert hasattr(indexer, 'convert_date')
    assert hasattr(indexer, 'convert_time')
    assert hasattr(indexer, 'convert_datetime')

  def test_indexer_convert_key(self):

    """ Test `Indexer.convert_key` """

    indexer = self.subject.Indexer
    sample_key = model.Key('Sample', 'key')
    converted = indexer.convert_key(sample_key)

    # interrogate converted key
    assert isinstance(converted, tuple)

  def test_indexer_convert_date(self):

    """ Test `Indexer.convert_date` """

    indexer = self.subject.Indexer
    sample_date = datetime.date(year=2014, month=7, day=29)
    converted = indexer.convert_date(sample_date)

    # interrogate converted date
    assert isinstance(converted, tuple)

  def test_indexer_convert_time(self):

    """ Test `Indexer.convert_time` """

    indexer = self.subject.Indexer
    sample_time = datetime.time(hour=12, minute=30)
    converted = indexer.convert_time(sample_time)

    # interrogate converted date
    assert isinstance(converted, tuple)

  def test_indexer_convert_datetime(self):

    """ Test `Indexer.convert_datetime` """

    indexer = self.subject.Indexer
    sample_datetime = datetime.datetime(year=2014, month=7, day=29, hour=12, minute=30)
    converted = indexer.convert_datetime(sample_datetime)

    # interrogate converted date
    assert isinstance(converted, tuple)


class GraphModelAdapterTests(IndexedModelAdapterTests):

  """ Tests `model.adapter.abstract.GraphModelAdapter` """

  __abstract__ = True
  subject = abstract.GraphModelAdapter

  def test_interface_compliance(self):

    """ Test `GraphModelAdapter` interface compliance """

    assert hasattr(self.subject, 'edges')
    assert hasattr(self.subject, 'neighbors')

  def test_make_vertex(self):

    """ Test `GraphModelAdapter` `Vertex` put """

    pass

  """
  def test_get_vertex(self):

    ''' Test `GraphModelAdapter` `Vertex` get '''

    pass

  def test_make_edge(self):

    ''' Test `GraphModelAdapter` `Edge` put '''

    pass

  def test_get_edge(self):

    ''' Test `GraphModelAdapter` `Edge` get '''

    pass

  def test_vertexes_connect(self):

    ''' Test connecting two `Vertex` records through an `Edge` '''

    pass

  def test_vertex_edges(self):

    ''' Test retrieving `Edges` for a `Vertex` with `GraphModelAdapter` '''

    pass

  def test_vertex_neighbors(self):

    ''' Test retrieving `Vertex` neighbors for a `Vertex` with `GraphModelAdapter` '''

    pass
  """


class DirectedGraphAdapterTests(GraphModelAdapterTests):

  """ Tests `model.adapter.abstract.DirectedGraphAdapter` """

  __abstract__ = True
  subject = abstract.DirectedGraphAdapter

  def test_interface_compliance(self):

    """ Test `DirectedGraphAdapter` interface compliance """

    assert hasattr(self.subject, 'heads')
    assert hasattr(self.subject, 'tails')

  """
  def test_vertex_heads(self):

    ''' Test retrieving `Edge`s ending at a particular `Vertex` '''

    pass

  def test_vertex_tails(self):

    ''' Test retrieving `Edge`s originating from a particular `Vertex` '''

    pass
  """
