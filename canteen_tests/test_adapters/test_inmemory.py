# -*- coding: utf-8 -*-

"""

  inmemory adapter tests
  ~~~~~~~~~~~~~~~~~~~~~~

  tests canteen's builtin inmemory DB engine.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

"""

# stdlib
import datetime

# canteen model API
from canteen import model
from canteen.model.adapter import inmemory

# abstract test bases
from .test_abstract import DirectedGraphAdapterTests


## Globals
_target = lambda k: k.flatten(True)[1]


class InMemoryModel(model.Model):

  """ Test model. """

  __adapter__ = inmemory.InMemoryAdapter

  string = basestring, {'required': True}
  integer = int, {'repeated': True}
  number = int, {'repeated': False}
  floating = float, {'required': False}
  date = datetime.datetime


class InMemoryAdapterTests(DirectedGraphAdapterTests):

  """ Tests `model.adapter.inmemory` """

  __abstract__ = False
  subject = inmemory.InMemoryAdapter

  def test_construct(self):

    """ Test basic construction of `InMemoryAdapter` """

    x = inmemory.InMemoryAdapter()
    assert x
    assert isinstance(x, inmemory.InMemoryAdapter)

  def test_invalid_get(self):

    """ Test requesting a key that doesn't exist """

    # get missing entity
    model_key = model.Key("Sample", "_____")
    entity = model_key.get()
    assert entity is None

  def test_named_entity_get_put(self):

    """ Test putting and getting an entity with a named key """

    # put entity
    m = InMemoryModel(
      key=model.Key(InMemoryModel.kind(), "NamedEntity"),
      string="suphomies",
      integer=[4, 5, 6, 7])
    m_k = m.put()

    assert _target(m_k) in inmemory._metadata['__key__']

    entities = []

    # simulate getting entity at key level
    explicit_key = model.Key(InMemoryModel.kind(), "NamedEntity")
    entity = explicit_key.get()
    entities.append(entity)

    # simulate getting entity at model level
    explicit_entity = InMemoryModel.get(name="NamedEntity")
    entities.append(explicit_entity)

    # test urlsafe-d key model-level get()
    urlsafed_entity = InMemoryModel.get(key=explicit_key.urlsafe())
    entities.append(urlsafed_entity)

    # test raw-d key model-level get()
    flattened = explicit_key.flatten(False)
    rawd_entity = InMemoryModel.get(key=flattened[1:])
    entities.append(rawd_entity)

    for entity in entities:
      # make sure things match on key level
      assert entity.string == "suphomies"
      assert len(entity.integer) == 4
      assert entity.key.id == "NamedEntity"
      assert entity.key.kind == InMemoryModel.kind()

  def test_id_entity_get_put(self):

    """ Test putting and getting an entity with an ID'd key """

    # put entity
    m = InMemoryModel(string="hello", integer=[1, 2, 3])
    m_k = m.put()

    assert _target(m_k) in inmemory._metadata['__key__']

    # make sure flags match
    assert m_k == m.key
    assert m_k.__persisted__
    assert m.__persisted__
    assert (not m.__dirty__)

    # simulate getting entity via urlsafe
    entity = InMemoryModel.get(m_k)

    # make sure things match
    assert entity.string == "hello"
    assert len(entity.integer) == 3
    assert entity.key.kind == InMemoryModel.kind()

  def test_delete_existing_entity_via_key(self):

    """ Test deleting an existing entity via `Key.delete()` """

    # put entity
    m = InMemoryModel(string="hello", integer=[1, 2, 3])
    m_k = m.put()

    # make sure it's known
    assert _target(m_k) in inmemory._metadata['__key__']

    # delete it
    res = m_k.delete()

    # make sure it's unknown and gone
    assert res
    assert _target(m_k) not in inmemory._metadata['__key__']

  def test_delete_existing_entity_via_model(self):

    """ Test deleting an existing entity via `Model.delete()` """

    # put entity
    m = InMemoryModel(string="hello", integer=[1, 2, 3])
    m_k = m.put()

    # make sure it's known
    assert _target(m_k) in inmemory._metadata['__key__']

    # delete it
    res = m.delete()

    # make sure it's unknown and gone
    assert res
    assert _target(m_k) not in inmemory._metadata['__key__']

  def test_delete_invalid_entity(self):

    """ Test deleting an invalid entity """

    # manufacture a key that shouldn't exist...
    m_k = model.Key("SampleKind", "____InvalidKey____")

    # make sure it's unknown
    assert _target(m_k) not in inmemory._metadata['__key__']

    # delete it
    res = m_k.delete()

    # make sure it's unknown, and we couldn't delete it
    assert (not res)
    assert _target(m_k) not in inmemory._metadata['__key__']

  def test_allocate_ids(self):

    """ Test allocating one and numerous ID's """

    # try allocating one ID
    next = inmemory.InMemoryAdapter.allocate_ids("Sample", 1)
    assert isinstance(next, int)

    # try allocating 10 ID's
    next_range = [i for i in inmemory.InMemoryAdapter.allocate_ids(*(
      model.Key, "Sample", 10))()]
    assert len(next_range) == 10
    for i in next_range:
      assert isinstance(i, int)

  def test_equality_query(self):

    """ Test equality queries with `InMemoryAdapter` """

    # make some models
    m = [
      InMemoryModel(string="soop", integer=[1, 2, 3]),
      InMemoryModel(string="soop", integer=[1, 2, 3]),
      InMemoryModel(string="soop", integer=[1, 2, 3])]

    for _m in m: _m.put()

    # single get
    q = InMemoryModel.query().filter(InMemoryModel.string == "soop")
    result = q.get()
    assert result.string == "soop"

    # submit query
    q = InMemoryModel.query().filter(InMemoryModel.string == "soop")
    result = q.fetch(limit=50)

    for r in result:
      assert r.string == "soop"

  def test_inequality_query(self):

    """ Test inequality queries with `InMemoryAdapter` """

    # make some models
    m = [
      InMemoryModel(string="soop", integer=[1, 2, 3]),
      InMemoryModel(string="soop", integer=[1, 2, 3]),
      InMemoryModel(string="soop", integer=[1, 2, 3]),
      InMemoryModel(string="sploop", integer=[1, 2])]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query().filter(InMemoryModel.string != "sploop")
    result = q.fetch(limit=50)

    assert len(result) > 0, (
      "got no results for inequality query"
      " (got '%s' from adapter '%s')" % (result, self.subject))

    for r in result:
      assert r.string != "sploop"

  def test_range_query(self):

    """ Test range queries with `InMemoryAdapter` """

    now = datetime.datetime.now()

    # make some models
    m = [
      InMemoryModel(string="soop", date=now + datetime.timedelta(days=1)),
      InMemoryModel(string="soop", date=now + datetime.timedelta(days=2)),
      InMemoryModel(string="soop", date=now + datetime.timedelta(days=3))]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query().filter(InMemoryModel.date > now)
    result = q.fetch(limit=50)

    for result_i in result:
      assert result_i.date > now

  def test_ancestry_query(self):

    """ Test ancestry queries with `InMemoryAdapter` """

    root = model.Key(InMemoryModel, 'heyo')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child')
    child2 = _key('child2')

    # make some models
    m = [
      InMemoryModel(key=root, string='soop'),
      InMemoryModel(key=child1, string='soop'),
      InMemoryModel(key=child2, string='soop')]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50)
    result = q.fetch()

    assert len(result) == 2

  def test_compound_query(self):

    """ Test compound queries with `InMemoryAdapter` """

    now = datetime.datetime.now()
    root = model.Key(InMemoryModel, 'hi')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')

    # make some models
    m = [
      InMemoryModel(key=root,
                    string="hithere",
                    date=now + datetime.timedelta(days=1)),
      InMemoryModel(key=child1,
                    string="hithere",
                    date=now + datetime.timedelta(days=2)),
      InMemoryModel(key=child2,
                    string="hithere",
                    date=now + datetime.timedelta(days=3)),
      InMemoryModel(key=child3,
                    string="noway",
                    date=now + datetime.timedelta(days=4))]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query(limit=50)
    q.filter(InMemoryModel.string == "hithere")
    q.filter(InMemoryModel.date > now)
    result = q.fetch()

    assert len(result) == 3

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50)
    q.filter(InMemoryModel.date > now)
    result = q.fetch()

    assert len(result) == 3

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50)
    q.filter(InMemoryModel.date > now)
    q.filter(InMemoryModel.string == "hithere")
    result = q.fetch()

    assert len(result) == 2

  def test_ascending_sort_string(self):

    """ Test an ASC sort on a string property with `InMemoryAdapter` """

    root = model.Key(InMemoryModel, 'sorted-string')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')
    child4 = _key('child4')

    # make some models
    m = [
      InMemoryModel(key=child1, string="aardvark"),
      InMemoryModel(key=child2, string="blasphemy"),
      InMemoryModel(key=child3, string="xylophone"),
      InMemoryModel(key=child4, string="yompin")
    ]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50).sort(+InMemoryModel.string)
    result = q.fetch()

    assert len(result) == 4

    for l, r in zip(result, reversed(("aardvark",
                                      "blasphemy",
                                      "xylophone",
                                      "yompin"))):
      assert l.string == r

  def test_descending_sort_string(self):

    """ Test a DSC sort on a string property with `InMemoryAdapter` """

    root = model.Key(InMemoryModel, 'sorted-string-2')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')
    child4 = _key('child4')

    # make some models
    m = [
      InMemoryModel(key=child1, string="aardvark"),
      InMemoryModel(key=child2, string="blasphemy"),
      InMemoryModel(key=child3, string="xylophone"),
      InMemoryModel(key=child4, string="yompin")]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50).sort(-InMemoryModel.string)
    result = q.fetch()

    assert len(result) == 4

    for l, r in zip(result, ("aardvark", "blasphemy", "xylophone", "yompin")):
      assert l.string == r

  def test_ascending_sort_integer(self):

    """ Test an ASC sort on an integer property with `InMemoryAdapter` """

    root = model.Key(InMemoryModel, 'sorted-int')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')
    child4 = _key('child4')

    # make some models
    m = [
      InMemoryModel(key=child1, string="aardvark", number=5),
      InMemoryModel(key=child2, string="blasphemy", number=6),
      InMemoryModel(key=child3, string="xylophone", number=7),
      InMemoryModel(key=child4, string="yompin", number=8)]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50).sort(+InMemoryModel.number)
    result = q.fetch()

    assert len(result) == 4

    for l, r in zip(result, (5, 6, 7, 8)):
      assert l.number == r

  def test_descending_sort_integer(self):

    """ Test a DSC sort on an integer property with `InMemoryAdapter` """

    root = model.Key(InMemoryModel, 'sorted-int-2')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')
    child4 = _key('child4')

    # make some models
    m = [
      InMemoryModel(key=child1, string="aardvark", number=5),
      InMemoryModel(key=child2, string="blasphemy", number=6),
      InMemoryModel(key=child3, string="xylophone", number=7),
      InMemoryModel(key=child4, string="yompin", number=8)]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50).sort(-InMemoryModel.number)
    result = q.fetch()

    assert len(result) == 4

    for l, r in zip(result, reversed((5, 6, 7, 8))):
      assert l.number == r

  def test_ascending_sort_float(self):

    """ Test an ASC sort on a float property with `InMemoryAdapter` """

    root = model.Key(InMemoryModel, 'sorted-float')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')
    child4 = _key('child4')

    # make some models
    m = [
      InMemoryModel(key=child1, string="aardvark", floating=5.5),
      InMemoryModel(key=child2, string="blasphemy", floating=6.5),
      InMemoryModel(key=child3, string="xylophone", floating=7.5),
      InMemoryModel(key=child4, string="yompin", floating=8.5)]

    for _m in m: _m.put()

    # submit query
    q = (
     InMemoryModel.query(ancestor=root, limit=50).sort(+InMemoryModel.floating))
    result = q.fetch()

    assert len(result) == 4

    for l, r in zip(result, (5.5, 6.5, 7.5, 8.5)):
      assert l.floating == r

  def test_descending_sort_float(self):

    """ Test a DSC sort on a float property with `InMemoryAdapter` """

    root = model.Key(InMemoryModel, 'sorted-float')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')
    child4 = _key('child4')

    # make some models
    m = [
      InMemoryModel(key=child1, string="aardvark", floating=5.5),
      InMemoryModel(key=child2, string="blasphemy", floating=6.5),
      InMemoryModel(key=child3, string="xylophone", floating=7.5),
      InMemoryModel(key=child4, string="yompin", floating=8.5)]

    for _m in m: _m.put()

    # submit query
    q = (
     InMemoryModel.query(ancestor=root, limit=50).sort(-InMemoryModel.floating))
    result = q.fetch()

    assert len(result) == 4

    for l, r in zip(result, reversed((5.5, 6.5, 7.5, 8.5))):
      assert l.floating == r

  def test_ascending_sort_datetime(self):

    """ Test an ASC sort on a `datetime` property with `InMemoryAdapter` """

    now = datetime.datetime.now()
    later = lambda n: now + datetime.timedelta(days=n)
    root = model.Key(InMemoryModel, 'sorted-datetime')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')
    child4 = _key('child4')

    # make some models
    m = [
      InMemoryModel(key=child1, string="aardvark", date=later(1)),
      InMemoryModel(key=child2, string="blasphemy", date=later(2)),
      InMemoryModel(key=child3, string="xylophone", date=later(3)),
      InMemoryModel(key=child4, string="yompin", date=later(4))]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50).sort(+InMemoryModel.date)
    result = q.fetch()

    assert len(result) == 4

    for l, r in zip(result, (later(1), later(2), later(3), later(4))):
      assert l.date == r

  def test_descending_sort_datetime(self):

    """ Test a DSC sort on a `datetime` property with `InMemoryAdapter` """

    now = datetime.datetime.now()
    later = lambda n: now + datetime.timedelta(days=n)
    root = model.Key(InMemoryModel, 'sorted-datetime')
    _key = lambda x: model.Key(InMemoryModel, x, parent=root)
    child1 = _key('child1')
    child2 = _key('child2')
    child3 = _key('child3')
    child4 = _key('child4')

    # make some models
    m = [
      InMemoryModel(key=child1, string="aardvark", date=later(1)),
      InMemoryModel(key=child2, string="blasphemy", date=later(2)),
      InMemoryModel(key=child3, string="xylophone", date=later(3)),
      InMemoryModel(key=child4, string="yompin", date=later(4))]

    for _m in m: _m.put()

    # submit query
    q = InMemoryModel.query(ancestor=root, limit=50).sort(-InMemoryModel.date)
    result = q.fetch()

    assert len(result) == 4

    for l, r in zip(result, reversed((later(1), later(2), later(3), later(4)))):
      assert l.date == r
