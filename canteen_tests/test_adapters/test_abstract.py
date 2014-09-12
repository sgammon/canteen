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


class TestGraphPerson(model.Vertex):

  """ simple test person object """

  name = str, {'indexed': True}


class TestGraphFriends(TestGraphPerson > TestGraphPerson):

  """ simple test friends edge """

  year_met = int, {'indexed': True}


class TestGraphGift(TestGraphPerson >> TestGraphPerson):

  """ simple directed gift edge """

  price = float, {'indexed': True}


class AbstractModelAdapterTests(FrameworkTest):

  """ Tests `model.adapter.abstract.ModelAdapter` """

  __abstract__ = True
  subject = abstract.ModelAdapter

  def _construct(self):

    """ Construct a copy of the local adapter. """

    # set to testing mode
    if hasattr(self.subject, '__testing__'):
      self.subject.__testing__ = True
    return self.subject()

  def test_abstract(self):

    """ Test `ModelAdapter` interface abstractness """

    if getattr(self, '__abstract__', False):
      with self.assertRaises(TypeError):
        self._construct()
    else:  # pragma: no cover
      self._construct()
    return getattr(self, '__abstract__', False)

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
    sample_datetime = datetime.datetime(year=2014,
                                        month=7,
                                        day=29,
                                        hour=12,
                                        minute=30)
    converted = indexer.convert_datetime(sample_datetime)

    # interrogate converted date
    assert isinstance(converted, tuple)


class GraphModelAdapterTests(IndexedModelAdapterTests):

  """ Tests `model.adapter.abstract.GraphModelAdapter` """

  __abstract__ = True
  subject = abstract.GraphModelAdapter

  def test_make_vertex_nokeyname(self):

    """ Test `GraphModelAdapter` `Vertex` put with no keyname """

    if not self.test_abstract():
      t = TestGraphPerson(name="Steve")
      k = t.put(adapter=self.subject())

      assert isinstance(t, TestGraphPerson)
      assert isinstance(k, model.Key)
      assert isinstance(k, model.VertexKey)
      assert isinstance(k.id, (int, long))

  def test_make_vertex_keyname(self):

    """ Test `GraphModelAdapter` `Vertex` put with a keyname """

    if not self.test_abstract():
      t = TestGraphPerson(key=model.VertexKey(TestGraphPerson, "steve"),
                          name="Steve")
      k = t.put(adapter=self.subject())

      assert isinstance(t, TestGraphPerson)
      assert isinstance(k, model.Key)
      assert isinstance(k, model.VertexKey)
      assert isinstance(k.id, basestring)
      return t

  def test_get_vertex(self):

    """ Test `GraphModelAdapter` `Vertex` get """

    if not self.test_abstract():
      x = self.test_make_vertex_keyname()
      pulled = TestGraphPerson.get(x.key, adapter=self.subject())

      assert pulled.key == x.key
      assert isinstance(pulled.key, model.Key)
      assert isinstance(pulled.key, model.VertexKey)
      assert isinstance(pulled.key.id, basestring)

  def test_make_edge_nokeyname(self):

    """ Test `GraphModelAdapter` `Edge` put with no keyname """

    if not self.test_abstract():
      bob = TestGraphPerson(key=model.VertexKey(TestGraphPerson, "bob"),
                          name="Bob")
      k = bob.put(adapter=self.subject())

      assert isinstance(bob, TestGraphPerson)
      assert isinstance(k, model.Key)
      assert isinstance(k, model.VertexKey)
      assert isinstance(k.id, basestring)

      steve = self.test_make_vertex_keyname()
      f = TestGraphFriends(bob, steve)
      ek = f.put(adapter=self.subject())

      assert isinstance(ek, model.EdgeKey)
      assert isinstance(ek.id, (int, long))
      assert isinstance(f, TestGraphFriends)

  def test_make_edge_keyname(self):

    """ Test `GraphModelAdapter` `Edge` put with a keyname """

    if not self.test_abstract():

      bob = TestGraphPerson(key=model.VertexKey(TestGraphPerson, "bob"),
                            name="Bob")
      k = bob.put(adapter=self.subject())

      assert isinstance(bob, TestGraphPerson)
      assert isinstance(k, model.Key)
      assert isinstance(k, model.VertexKey)
      assert isinstance(k.id, basestring)

      steve = self.test_make_vertex_keyname()
      _orig_ek = model.EdgeKey(TestGraphFriends, "some-friendship")
      f = TestGraphFriends(bob, steve, key=_orig_ek)
      ek = f.put(adapter=self.subject())

      assert isinstance(ek, model.EdgeKey)
      assert isinstance(ek.id, basestring)
      assert isinstance(f, TestGraphFriends)
      assert ek.id == "some-friendship"

      return bob, steve, f

  def test_get_edge(self):

    """ Test `GraphModelAdapter` `Edge` get """

    if not self.test_abstract():
      bob, steve, friendship = self.test_make_edge_keyname()

      # fetch by key
      _f = TestGraphFriends.get(friendship.key, adapter=self.subject())

      assert isinstance(_f.key, model.Key)
      assert isinstance(_f.key, model.EdgeKey)
      assert isinstance(_f.key.id, basestring)
      assert _f.key.id == "some-friendship"
      assert _f.key.kind == "TestGraphFriends"

  def test_vertex_edges(self):

    """ Test retrieving `Edges` for a `Vertex` with `GraphModelAdapter` """

    if not self.test_abstract():
      bob, steve, friendship = self.test_make_edge_keyname()

      # friendship edge should appear for both vertexes
      _q = bob.edges(keys_only=True).fetch(adapter=self.subject(), limit=10)
      assert friendship.key in _q, (
        "expected friendship key but got:"
        " '%s' with adapter '%s'" % (
          [i for i in _q], repr(self.subject())))

      assert friendship.key in (
        steve.edges(keys_only=True).fetch(adapter=self.subject(), limit=10))
      assert "Edges" in repr(steve.edges(keys_only=True))
      assert "CONTAINS" in repr(steve.edges(keys_only=True))

  def test_vertex_neighbors(self):

    """ Test retrieving `Vertex`es for a `Vertex` with `GraphModelAdapter` """

    if not self.test_abstract():
      bob, steve, friendship = self.test_make_edge_keyname()

      # see if we can get bob's friends, which should include steve
      _q = bob.neighbors(keys_only=True).fetch(adapter=self.subject(), limit=10)
      assert steve.key in _q, (
        "failed to find steve's key in bob's neighbors."
        " instead, got '%s' for adapter '%s'" % (
          [i for i in _q], repr(self.subject())))

      # see if we can get steve's friends, which should include bob
      assert bob.key in (
        steve.neighbors(keys_only=True).fetch(adapter=self.subject(), limit=10))
      assert "Neighbors" in repr(steve.neighbors(keys_only=True))
      assert "CONTAINS" in repr(steve.neighbors(keys_only=True))


class DirectedGraphAdapterTests(GraphModelAdapterTests):

  """ Tests `model.adapter.abstract.DirectedGraphAdapter` """

  __abstract__ = True
  subject = abstract.DirectedGraphAdapter

  def test_make_directed_edge_nokeyname(self):

    """ Test saving a directed `Edge` with no keyname """

    if not self.test_abstract():
      bob = TestGraphPerson(key=model.VertexKey(TestGraphPerson, "bob"),
                          name="Bob")
      k = bob.put(adapter=self.subject())

      assert isinstance(bob, TestGraphPerson)
      assert isinstance(k, model.Key)
      assert isinstance(k, model.VertexKey)
      assert isinstance(k.id, basestring)

      steve = self.test_make_vertex_keyname()
      f = TestGraphGift(bob, steve)
      ek = f.put(adapter=self.subject())

      assert bob.key == f.source
      assert steve.key in f.target

      assert isinstance(ek, model.EdgeKey)
      assert isinstance(ek.id, (int, long))
      assert isinstance(f, TestGraphGift)

  def test_make_directed_edge_keyname(self):

    """ Test saving a directed `Edge` with a keyname """

    if not self.test_abstract():

      bob = TestGraphPerson(key=model.VertexKey(TestGraphPerson, "bob"),
                            name="Bob")
      k = bob.put(adapter=self.subject())

      assert isinstance(k, model.Key), (
        "instead of a key, got back the object: '%s'" % k)
      assert isinstance(bob, TestGraphPerson)
      assert isinstance(k, model.VertexKey)
      assert isinstance(k.id, basestring)

      steve = self.test_make_vertex_keyname()
      _orig_ek = model.EdgeKey(TestGraphGift, "some-gift")
      f = TestGraphGift(bob, steve, key=_orig_ek)

      ek = f.put(adapter=self.subject())

      assert isinstance(ek, model.EdgeKey)
      assert isinstance(ek.id, basestring)
      assert isinstance(f, TestGraphGift)
      assert ek.id == "some-gift"

      assert bob.key == f.source
      assert steve.key in f.target

      return bob, steve, f

  def test_get_directed_edge_nokeyname(self):

    """ Test retrieving a directed `Edge` by keyname """

    if not self.test_abstract():
      bob, steve, gift = self.test_make_directed_edge_keyname()

      # fetch by key
      _f = TestGraphGift.get(gift.key, adapter=self.subject())

      assert isinstance(_f.key, model.Key)
      assert isinstance(_f.key, model.EdgeKey)
      assert isinstance(_f.key.id, basestring)
      assert _f.key.id == "some-gift"
      assert _f.key.kind == "TestGraphGift"

  def test_edge_heads(self):

    """ Test retrieving incoming `Edge`s ending at a particular `Vertex` """

    if not self.test_abstract():
      bob, steve, gift = self.test_make_directed_edge_keyname()

      # friendship edge should appear for both vertexes
      _q = bob.edges(tails=False, keys_only=True)\
          .fetch(adapter=self.subject(), limit=10)
      assert gift.key not in _q, (
            "found gift's key among bob's edges heads, but shouldn't have."
            " instead, got: '%s' with adapter '%s'" % (
              [i for i in _q], repr(self.subject())))

      _q = steve.edges(tails=False, keys_only=True)\
          .fetch(adapter=self.subject(), limit=10)
      assert gift.key in _q, (
            "couldn't find gift's key among steve's edges heads."
            " instead, got: '%s' with adapter '%s'" % (
              [i for i in _q], repr(self.subject())))

  def test_edge_tails(self):

    """ Test retrieving outbound `Edge`s coming from a particular `Vertex` """

    if not self.test_abstract():
      bob, steve, gift = self.test_make_directed_edge_keyname()

      # friendship edge should appear for both vertexes
      _q = bob.edges(tails=True, keys_only=True)\
          .fetch(adapter=self.subject(), limit=10)
      assert gift.key in _q
      _q = steve.edges(tails=True, keys_only=True)\
          .fetch(adapter=self.subject(), limit=10)
      assert gift.key not in _q

  def test_neighbor_heads(self):

    """ Test retrieving incoming `Vertex`s ending at a particular `Vertex` """

    if not self.test_abstract():
      bob, steve, gift = self.test_make_directed_edge_keyname()

      # see if we can get steve's friends, which should include bob
      _q = steve.neighbors(tails=False, keys_only=True)\
          .fetch(adapter=self.subject(), limit=10)
      assert bob.key in _q, (
            "didn't find bob's key among steve's friends."
            " instead, got: '%s' with adapter '%s'" % (
              [i for i in _q], repr(self.subject())))

  def test_neighbor_tails(self):

    """ Test retrieving outbound `Vertex`s coming from a particular `Vertex` """

    if not self.test_abstract():
      bob, steve, gift = self.test_make_directed_edge_keyname()

      # see if we can get bob's friends, which should include steve
      assert steve.key in bob.neighbors(tails=True, keys_only=True)\
          .fetch(adapter=self.subject(), limit=10)
