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
from canteen import test

# canteen model API
from canteen import model
from canteen.model.adapter import abstract


## Globals
_target = lambda k: k.flatten(True)[1]


class SampleModel(model.Model):

  """ Test model. """

  string = basestring, {'required': True}
  integer = int, {'repeated': True}
  number = int, {'repeated': False}
  floating = float, {'required': False}
  date = datetime.datetime


class TestGraphPerson(model.Vertex):

  """ simple test person object """

  name = str, {'indexed': True}


class TestGraphFriends(TestGraphPerson > TestGraphPerson):

  """ simple test friends edge """

  year_met = int, {'indexed': True}


class TestGraphGift(TestGraphPerson >> TestGraphPerson):

  """ simple directed gift edge """

  price = float, {'indexed': True}


class AbstractModelAdapterTests(test.FrameworkTest):

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
    assert hasattr(self.subject, 'get_multi')
    assert hasattr(self.subject, 'put')
    assert hasattr(self.subject, 'delete')
    assert hasattr(self.subject, 'allocate_ids')
    assert hasattr(self.subject, 'encode_key')

  def test_construct(self):

    """ Test basic `ModelAdapter` construction """

    if self.__abstract__:
      with self.assertRaises(TypeError):
        self._construct()
    else:
      x = self._construct()
      assert x
      assert isinstance(x, self.subject)

  def test_invalid_get(self):

    """ Test fetching a key that doesn't exist """

    if not self.__abstract__:
      # get missing entity
      model_key = model.Key("Sample", "_____")
      entity = model_key.get(adapter=self._construct())
      assert entity is None

  def test_named_entity_get_put(self):

    """ Test putting and getting an entity with a named key """

    if not self.__abstract__:
      # put entity
      m = SampleModel(
        key=model.Key(SampleModel.kind(), "NamedEntity"),
        string="suphomies",
        integer=[4, 5, 6, 7])
      m_k = m.put(adapter=self._construct())

      entities = []

      # simulate getting entity at key level
      explicit_key = model.Key(SampleModel.kind(), "NamedEntity")
      entity = explicit_key.get()
      entities.append(entity)

      # simulate getting entity at model level
      explicit_entity = SampleModel.get(name="NamedEntity")
      entities.append(explicit_entity)

      # test urlsafe-d key model-level get()
      urlsafed_entity = SampleModel.get(key=explicit_key.urlsafe())
      entities.append(urlsafed_entity)

      # test raw-d key model-level get()
      flattened = explicit_key.flatten(False)
      rawd_entity = SampleModel.get(key=flattened[1:])
      entities.append(rawd_entity)

      for entity in entities:
        # make sure things match on key level
        assert entity.string == "suphomies"
        assert len(entity.integer) == 4
        assert entity.key.id == "NamedEntity"
        assert entity.key.kind == SampleModel.kind()

  def test_id_entity_get_put(self):

    """ Test putting and getting an entity with an ID'd key """

    if not self.__abstract__:
      # put entity
      m = SampleModel(string="hello", integer=[1, 2, 3])
      m_k = m.put(adapter=self._construct())

      # make sure flags match
      assert m_k == m.key
      assert m_k.__persisted__
      assert m.__persisted__
      assert (not m.__dirty__)

      # simulate getting entity via urlsafe
      entity = SampleModel.get(m_k, adapter=self._construct())

      # make sure things match
      assert entity.string == "hello"
      assert len(entity.integer) == 3
      assert entity.key.kind == SampleModel.kind()

  def test_entity_multiget(self):

    """ Test retrieving multiple entities at once via `get_multi` """

    if not self.__abstract__:
      # put some entities
      entities = [
        SampleModel(string='hi', integer=[1, 2, 3]),
        SampleModel(string='sup', integer=[4, 5, 6]),
        SampleModel(string='hola', integer=[7, 8, 9])]

      keys = []
      for entity in entities:
        keys.append(entity.put(adapter=self._construct()))

      # retrieve entities in bulk
      _results = []
      for key, entity in zip(keys,
                      SampleModel.get_multi(keys, adapter=self._construct())):
        assert key.kind == SampleModel.kind()
        assert entity, (
          "failed to retrieve entity with adapter '%s'" % self._construct())
        assert entity.string in ('hi', 'sup', 'hola')
        assert len(entity.integer) == 3
        _results.append(entity)
      assert len(_results) == 3

  def test_delete_existing_entity_via_key(self):

    """ Test deleting an existing entity via `Key.delete()` """

    if not self.__abstract__:
      # put entity
      m = SampleModel(string="hello", integer=[1, 2, 3])
      m_k = m.put(adapter=self._construct())

      # delete it
      res = m_k.delete(adapter=self._construct())

      # make sure it's unknown and gone
      assert res
      assert not SampleModel.get(m_k, adapter=self._construct())

  def test_delete_existing_entity_via_model(self):

    """ Test deleting an existing entity via `Model.delete()` """

    if not self.__abstract__:
      # put entity
      m = SampleModel(string="hello", integer=[1, 2, 3])
      m_k = m.put(adapter=self._construct())

      # delete it
      res = m.delete(adapter=self._construct())

      # make sure it's unknown and gone
      assert res
      assert not SampleModel.get(m_k, adapter=self._construct())

  def test_delete_invalid_entity(self):

    """ Test deleting an invalid entity """

    if not self.__abstract__:
      # manufacture a key that shouldn't exist...
      m_k = model.Key("SampleKind", "____InvalidKey____")

      # make sure it's unknown
      assert not SampleModel.get(m_k, adapter=self._construct())

      # delete it
      res = m_k.delete(adapter=self._construct())

      # make sure it's unknown, and we couldn't delete it
      assert (not res)
      assert not SampleModel.get(m_k, adapter=self._construct())

  def test_allocate_ids(self):

    """ Test allocating one and numerous ID's """

    if not self.__abstract__:
      # try allocating one ID
      next = self._construct().allocate_ids(model.Key, "SampleModel", 1)
      assert isinstance(next, int)

      # try allocating 10 ID's
      next_range = [i for i in self._construct().allocate_ids(*(
        model.Key, "Sample", 10))()]
      assert len(next_range) == 10
      for i in next_range:
        assert isinstance(i, int)


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

  def test_equality_query(self):

    """ Test equality queries with `IndexedMemoryAdapter` """

    if not self.__abstract__:

      # make some models
      m = [
        SampleModel(string="soop", integer=[1, 2, 3]),
        SampleModel(string="soop", integer=[1, 2, 3]),
        SampleModel(string="soop", integer=[1, 2, 3])]

      for _m in m: _m.put(adapter=self._construct())

      # single get
      q = SampleModel.query().filter(SampleModel.string == "soop")

      result = q.get(adapter=self._construct())
      assert result.string == "soop"

      # submit query
      q = SampleModel.query().filter(SampleModel.string == "soop")
      result = q.fetch(limit=50, adapter=self._construct())

      for r in result:
        assert r.string == "soop"

  def test_inequality_query(self):

    """ Test inequality queries with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      # make some models
      m = [
        SampleModel(string="soop", integer=[1, 2, 3]),
        SampleModel(string="soop", integer=[1, 2, 3]),
        SampleModel(string="soop", integer=[1, 2, 3]),
        SampleModel(string="sploop", integer=[1, 2])]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query().filter(SampleModel.string != "sploop")
      result = q.fetch(limit=50, adapter=self._construct())

      assert len(result) > 0, (
        "got no results for inequality query"
        " (got '%s' from adapter '%s')" % (result, self.subject))

      for r in result:
        assert r.string != "sploop"

  def test_range_query(self):

    """ Test range queries with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      now = datetime.datetime.now()

      # make some models
      m = [
        SampleModel(string="soop", date=now + datetime.timedelta(days=1)),
        SampleModel(string="soop", date=now + datetime.timedelta(days=2)),
        SampleModel(string="soop", date=now + datetime.timedelta(days=3))]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query().filter(SampleModel.date > now)
      result = q.fetch(limit=50, adapter=self._construct())

      for result_i in result:
        assert result_i.date > now

  def test_ancestry_query(self):

    """ Test ancestry queries with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      root = model.Key(SampleModel, 'heyo')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child')
      child2 = _key('child2')

      # make some models
      m = [
        SampleModel(key=root, string='soop'),
        SampleModel(key=child1, string='soop'),
        SampleModel(key=child2, string='soop')]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query(ancestor=root, limit=50, adapter=self._construct())
      result = q.fetch()

      assert len(result) == 2

  def test_compound_query(self):

    """ Test compound queries with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      now = datetime.datetime.now()
      root = model.Key(SampleModel, 'hi')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')

      # make some models
      m = [
        SampleModel(key=root,
                      string="hithere",
                      date=now + datetime.timedelta(days=1)),
        SampleModel(key=child1,
                      string="hithere",
                      date=now + datetime.timedelta(days=2)),
        SampleModel(key=child2,
                      string="hithere",
                      date=now + datetime.timedelta(days=3)),
        SampleModel(key=child3,
                      string="noway",
                      date=now + datetime.timedelta(days=4))]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query(limit=50)
      q.filter(SampleModel.string == "hithere")
      q.filter(SampleModel.date > now)
      result = q.fetch(adapter=self._construct())

      assert len(result) == 3

      # submit query
      q = SampleModel.query(ancestor=root, limit=50)
      q.filter(SampleModel.date > now)
      result = q.fetch(adapter=self._construct())

      assert len(result) == 3

      # submit query
      q = SampleModel.query(ancestor=root, limit=50)
      q.filter(SampleModel.date > now)
      q.filter(SampleModel.string == "hithere")
      result = q.fetch(adapter=self._construct())

      assert len(result) == 2

  def test_ascending_sort_string(self):

    """ Test an ASC sort on a string property with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      root = model.Key(SampleModel, 'sorted-string')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')
      child4 = _key('child4')

      # make some models
      m = [
        SampleModel(key=child1, string="aardvark"),
        SampleModel(key=child2, string="blasphemy"),
        SampleModel(key=child3, string="xylophone"),
        SampleModel(key=child4, string="yompin")]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query(ancestor=root, limit=50).sort(+SampleModel.string)
      result = q.fetch(adapter=self._construct())

      assert len(result) == 4

      for l, r in zip(result, reversed(("aardvark",
                                        "blasphemy",
                                        "xylophone",
                                        "yompin"))):
        assert l.string == r

  def test_descending_sort_string(self):

    """ Test a DSC sort on a string property with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      root = model.Key(SampleModel, 'sorted-string-2')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')
      child4 = _key('child4')

      # make some models
      m = [
        SampleModel(key=child1, string="aardvark"),
        SampleModel(key=child2, string="blasphemy"),
        SampleModel(key=child3, string="xylophone"),
        SampleModel(key=child4, string="yompin")]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query(ancestor=root, limit=50).sort(-SampleModel.string)
      result = q.fetch(adapter=self._construct())

      assert len(result) == 4

      for l, r in zip(result, ("aardvark", "blasphemy", "xylophone", "yompin")):
        assert l.string == r

  def test_ascending_sort_integer(self):

    """ Test an ASC sort on an integer property with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      root = model.Key(SampleModel, 'sorted-int')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')
      child4 = _key('child4')

      # make some models
      m = [
        SampleModel(key=child1, string="aardvark", number=5),
        SampleModel(key=child2, string="blasphemy", number=6),
        SampleModel(key=child3, string="xylophone", number=7),
        SampleModel(key=child4, string="yompin", number=8)]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query(ancestor=root, limit=50).sort(+SampleModel.number)
      result = q.fetch(adapter=self._construct())

      assert len(result) == 4

      for l, r in zip(result, (5, 6, 7, 8)):
        assert l.number == r

  def test_descending_sort_integer(self):

    """ Test a DSC sort on an integer property with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      root = model.Key(SampleModel, 'sorted-int-2')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')
      child4 = _key('child4')

      # make some models
      m = [
        SampleModel(key=child1, string="aardvark", number=5),
        SampleModel(key=child2, string="blasphemy", number=6),
        SampleModel(key=child3, string="xylophone", number=7),
        SampleModel(key=child4, string="yompin", number=8)]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query(ancestor=root, limit=50).sort(-SampleModel.number)
      result = q.fetch(adapter=self._construct())

      assert len(result) == 4

      for l, r in zip(result, reversed((5, 6, 7, 8))):
        assert l.number == r

  def test_ascending_sort_float(self):

    """ Test an ASC sort on a float property with `IndexedMemoryAdapter` """

    if not self.__abstract__:
      root = model.Key(SampleModel, 'sorted-float')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')
      child4 = _key('child4')

      # make some models
      m = [
        SampleModel(key=child1, string="aardvark", floating=5.5),
        SampleModel(key=child2, string="blasphemy", floating=6.5),
        SampleModel(key=child3, string="xylophone", floating=7.5),
        SampleModel(key=child4, string="yompin", floating=8.5)]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = (
        SampleModel.query(ancestor=root, limit=50).sort(
          +SampleModel.floating))
      result = q.fetch(adapter=self._construct())

      assert len(result) == 4

      for l, r in zip(result, (5.5, 6.5, 7.5, 8.5)):
        assert l.floating == r

  def test_descending_sort_float(self):

    """ Test a DSC sort on a float property with `IndexedModelAdapter` """

    if not self.__abstract__:
      root = model.Key(SampleModel, 'sorted-float')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')
      child4 = _key('child4')

      # make some models
      m = [
        SampleModel(key=child1, string="aardvark", floating=5.5),
        SampleModel(key=child2, string="blasphemy", floating=6.5),
        SampleModel(key=child3, string="xylophone", floating=7.5),
        SampleModel(key=child4, string="yompin", floating=8.5)]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = (
        SampleModel.query(ancestor=root, limit=50).sort(
          -SampleModel.floating))
      result = q.fetch(adapter=self._construct())

      assert len(result) == 4

      for l, r in zip(result, reversed((5.5, 6.5, 7.5, 8.5))):
        assert l.floating == r

  def test_ascending_sort_datetime(self):

    """ Test an ASC sort on a `datetime` property with `IndexedModelAdapter` """

    if not self.__abstract__:
      now = datetime.datetime.now()
      later = lambda n: now + datetime.timedelta(days=n)
      root = model.Key(SampleModel, 'sorted-datetime')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')
      child4 = _key('child4')

      # make some models
      m = [
        SampleModel(key=child1, string="aardvark", date=later(1)),
        SampleModel(key=child2, string="blasphemy", date=later(2)),
        SampleModel(key=child3, string="xylophone", date=later(3)),
        SampleModel(key=child4, string="yompin", date=later(4))]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query(ancestor=root, limit=50).sort(+SampleModel.date)
      result = q.fetch(adapter=self._construct())

      assert len(result) == 4

      for l, r in zip(result, (later(1), later(2), later(3), later(4))):
        assert l.date == r

  def test_descending_sort_datetime(self):

    """ Test a DSC sort on a `datetime` property with `IndexedModelAdapter` """

    if not self.__abstract__:
      now = datetime.datetime.now()
      later = lambda n: now + datetime.timedelta(days=n)
      root = model.Key(SampleModel, 'sorted-datetime')
      _key = lambda x: model.Key(SampleModel, x, parent=root)
      child1 = _key('child1')
      child2 = _key('child2')
      child3 = _key('child3')
      child4 = _key('child4')

      # make some models
      m = [
        SampleModel(key=child1, string="aardvark", date=later(1)),
        SampleModel(key=child2, string="blasphemy", date=later(2)),
        SampleModel(key=child3, string="xylophone", date=later(3)),
        SampleModel(key=child4, string="yompin", date=later(4))]

      for _m in m: _m.put(adapter=self._construct())

      # submit query
      q = SampleModel.query(ancestor=root, limit=50).sort(-SampleModel.date)
      result = q.fetch(adapter=self._construct())

      assert len(result) == 4

      for l, r in zip(result, reversed((
            later(1), later(2), later(3), later(4)))):
        assert l.date == r


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
