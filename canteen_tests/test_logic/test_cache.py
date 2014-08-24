# -*- coding: utf-8 -*-

'''

  cache logic tests
  ~~~~~~~~~~~~~~~~~

  tests builtin caching-related logic.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

'''

# stdlib
import weakref

# testing
from canteen import test
from canteen.logic import cache


class PersistentCacheTests(test.FrameworkTest):

  ''' Tests ``Caching.PersistentCache``. '''

  def test_should_expire(self):

    ''' Test that `PersistentCache` items never expire '''

    p = cache.Caching.PersistentCache()
    assert not p.should_expire('anything', 12345)

  def test_on_tick(self):

    ''' Test that `PersistentCache` ticks don't trigger sweeps '''

    p = cache.Caching.PersistentCache()
    assert p.tick(12345) is NotImplemented

  def test_spawn_default(self):

    ''' Test that `Caching.spawn` with default arguments gives default cache '''

    assert cache.Caching.spawn() is cache.Caching.spawn()

  def test_hard_flush(self):

    ''' Test that `Caching.flush` empties all local caches '''

    assert cache.Caching.set('hi', 5) == 5

    cache.Caching.flush()
    assert cache.Caching.get('hi') is None

  def test_default_cache_clear_named(self):

    ''' Test against `Cache` interface method `clear` with a name '''

    # set and get again then iterate
    c = cache.Caching.spawn('nukeme')
    d = cache.Caching.spawn('dontnukemebro')

    # try with dict
    assert c.set_multi({'sup': 5, 'blab': 10})
    assert c.get('sup') == 5
    assert c.get('blab') == 10
    assert d.set_multi({'sup': 5, 'blab': 10})
    assert d.get('sup') == 5
    assert d.get('blab') == 10

    cache.Caching.clear('nukeme')
    assert c.get('sup') is None
    assert c.get('blab') is None
    assert d.get('sup') == 5
    assert d.get('blab') == 10


class CacheEngineTests(test.FrameworkTest):

  ''' Tests ``cache.Cache.Engine`` object abstractness and interface '''

  subject = cache.Cache.Engine

  def _spawn_cache(self, name=None):

    ''' Utility to prepare a new cache with a default strategy and target. '''

    if self.subject is cache.Caching:
      return cache.Caching  # testing against default storage
    elif self.subject is cache.Cache.Engine:
      return cache.Caching.spawn()
    return cache.Caching.spawn(name or 'testing', {}, self.subject)

  def test_abstract(self):

    ''' Test that `Cache` is abstract and implementors are not '''

    if self.subject is cache.Cache.Engine:

      with self.assertRaises(TypeError):
        self.subject()

      return True
    return False

  def test_interface(self):

    ''' Test against the interface for a `Cache` '''

    assert hasattr(self.subject, 'get')
    assert hasattr(self.subject, 'get_multi')
    assert hasattr(self.subject, 'items')
    assert hasattr(self.subject, 'set')
    assert hasattr(self.subject, 'set_multi')
    assert hasattr(self.subject, 'delete')
    assert hasattr(self.subject, 'delete_multi')
    assert hasattr(self.subject, 'clear')

    # if not abstract, test against methods
    if not self.test_abstract():
      subj = self._spawn_cache()
      assert hasattr(subj, 'get')
      assert hasattr(subj, 'get_multi')
      assert hasattr(subj, 'set')
      assert hasattr(subj, 'set_multi')
      assert hasattr(subj, 'delete')
      assert hasattr(subj, 'delete_multi')
      assert hasattr(subj, 'clear')

  def test_cache_get_hit(self):

    ''' Test against `Cache` interface method `get` with hit '''

    if not self.test_abstract():

      # store an item and get it
      c = self._spawn_cache()
      c.set('sup', 5)
      assert c.get('sup') == 5

  def test_cache_get_miss(self):

    ''' Test against `Cache` interface method `get` with miss '''

    if not self.test_abstract():

      # store an item
      c = self._spawn_cache()
      assert c.get('blabble') is None

      # test with custom default
      assert c.get('bleebs', default=5) == 5

  def test_cache_items(self):

    ''' Test against `Cache` interface method `items` '''

    if not self.test_abstract():

      # store an item
      c = self._spawn_cache()
      assert c.set('blabble', 5) == 5
      assert c.set('bleebs', 10) == 10

      struct = dict(c.items())
      assert 'blabble' in struct
      assert 'bleebs' in struct
      assert struct['blabble'] == 5
      assert struct['bleebs'] == 10

  def test_cache_set(self):

    ''' Test against `Cache` interface method `set` '''

    if not self.test_abstract():

      # set and get again
      c = self._spawn_cache()
      assert c.set('sup', 5) == 5
      assert c.get('sup') == 5

  def test_cache_delete(self):

    ''' Test against `Cache` interface method `delete` '''

    if not self.test_abstract():

      # set and get again then delete
      c = self._spawn_cache()
      assert c.set('sup', 5) == 5
      assert c.get('sup') == 5
      c.delete('sup')
      assert c.get('sup') is None

  def test_cache_get_multi(self):

    ''' Test against `Cache` interface method `get_multi` '''

    if not self.test_abstract():

      # set and get again then iterate
      c = self._spawn_cache()

      # try with dict
      assert c.set('sup', 5) == 5
      assert c.set('blab', 10) == 10
      result = c.get_multi(('sup', 'blab'))
      assert 'sup' in result
      assert result['sup'] == 5
      assert 'blab' in result
      assert result['blab'] == 10

  def test_cache_set_multi(self):

    ''' Test against `Cache` interface method `set_multi` '''

    if not self.test_abstract():

      # set and get again then iterate
      c = self._spawn_cache()

      # try with dict
      assert c.set_multi({'sup': 5, 'blab': 10})
      assert c.get('sup') == 5
      assert c.get('blab') == 10

  def test_cache_delete_multi(self):

    ''' Test against `Cache` interface method `delete_multi` '''

    if not self.test_abstract():

      # set and get again then iterate
      c = self._spawn_cache()

      # try with dict
      assert c.set_multi({'sup': 5, 'blab': 10})
      assert c.get('sup') == 5
      assert c.get('blab') == 10

      c.delete_multi(('sup', 'blab'))
      assert c.get('sup') is None
      assert c.get('blab') is None

  def test_cache_clear(self):

    ''' Test against `Cache` interface method `clear` '''

    if not self.test_abstract():

      # set and get again then iterate
      c = self._spawn_cache()

      # try with dict
      assert c.set_multi({'sup': 5, 'blab': 10})
      assert c.get('sup') == 5
      assert c.get('blab') == 10

      c.clear()
      assert c.get('sup') is None
      assert c.get('blab') is None


class ThreadcacheTests(CacheEngineTests):

  ''' Tests ``cache.Caching.Threadcache``. '''

  subject = cache.Caching.Threadcache

  def test_value_weakref(self):

    ''' Test that complex values are cached by weak reference '''

    class Something(object): pass
    x = Something()
    x.hi = 5

    y = self._spawn_cache()
    y.set('something', x)

    # make sure things are written as weakrefs
    assert 'something' in y.target
    assert isinstance(y.target['something'], tuple)
    assert isinstance(y.target['something'][0], weakref.ref)

    # make sure weakrefs are unwrapped on the way out
    assert not isinstance(y.get('something'), weakref.ref)


class DefaultThreadcacheTests(CacheEngineTests):

  ''' Tests ``cache.Caching``. '''

  subject = cache.Caching
