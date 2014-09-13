# -*- coding: utf-8 -*-

"""

  caching logic
  ~~~~~~~~~~~~~

  exposes simple logic for caching objects in-memory or in
  caching engines like ``memcached``.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import abc
import time
import weakref
import threading

# core and utils
from ..base import logic
from ..util import decorators


## Globals
_caches = {}
_default = (threading.local(), None)
_BUILTIN_TYPES = (int, float, str, list, dict, tuple, unicode, type(abc))


class Cache(object):

  """ Specifies an instance of a cache, that supports storage and retrieval of
      arbitrary native Python values.

      Attached to every :py:class:`Cache` is a ``Strategy`` and a ``Target``,
      specifying the management policy and underlying caching engine,
      respectively.

      Both components are extendable to create custom caching solutions. """

  class Engine(object):

    """  """

    target = None  # cache adapter/library
    strategy = None  # strategy to use for eviction

    __metaclass__ = abc.ABCMeta

    ## == Internals == ##
    def __init__(self, target, strategy=None):

      """ Initialize a new ``Cache``, utilizing ``target`` as a cache
          adapter/library ``strategy`` as a cache management policy.

          :param target: Target library or cache system.

          :param strategy: Cache management policy, extending
            ``Cache.Strategy``. """

      self.target, self.strategy = target, strategy

    #### ==== Read Methods ==== ####
    @abc.abstractmethod
    def get(self, key):

      """ Specifies abstract version of ``Cache.get``, which is used to retrieve
          cached items.

          :param key: Cached item's key.

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: Implementors must return the cached item stored at
            ``key``. """

      raise NotImplementedError('`Cache.get`'
                                ' is abstract.')  # pragma: no cover

    @abc.abstractmethod
    def get_multi(self, keys):

      """ Specifies abstract version of ``Cache.get_multi`, which is used to
          retrieve multiple cache items ine one call.

          :param keys: Iterable of cached item keys.

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: Implementors must return a dict of cached items cached
            items, or ``None``, according to that result's position in the
            original ``keys`` iterable. """

      raise NotImplementedError('`Cache.get_multi`'
                                ' is abstract.')  # pragma: no cover

    @abc.abstractmethod
    def items(self, timestamp):

      """ Specifies abstract version of ``Cache.items``, which is used to
          iterate over items in the cache, optionally current to ``timestamp``.

          This method is optional for implementors but must always be defined.
          If an implementing class wishes not to implement this method, it must
          return ``NotImplemented``.

          :param timestamp: Optionally only return cached items that were saved
            after the given ``datetime.datetime`` or integer Unix timestamp.

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: Implementors must either return ``NotImplemented`` (if they
            choose not to provide an ``items`` implementation) or an iterator
            that will yield ``(key, value)`` tuples of items in the cache,
            optionally current to ``timestamp``. """

      raise NotImplementedError('`Cache.items`'
                                ' is abstract.')  # pragma: no cover


    #### ==== Write Methods ==== ####
    @abc.abstractmethod
    def set(self, key, value):

      """ Specifies abstract version of ``Cache.set``, which is used to store
          individual items in the ``Cache``.

          :param key: String key the item should be stored at, for future
            reference.

          :param value: Raw value to be stored in the cache at ``key``.

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: Implementors must return the original value passed in to be
            cached at ``value``. """

      raise NotImplementedError('`Cache.set`'
                                ' is abstract.')  # pragma: no cover

    @abc.abstractmethod
    def set_multi(self, map):

      """ Specifies abstract version of ``Cache.set_multi``, which is used to
          write multiple items to the ``Cache`` in one call.

          :param map: Iterable of ``(key, value)`` tuples or ``dict`` of
            ``key=>value`` mappings that should be saved to the cache.

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: Implementors must return the original iterable or ``dict``
            of values passed in to be cached at ``map``. """

      raise NotImplementedError('`Cache.set_multi`'
                                ' is abstract.')  # pragma: no cover

    #### ==== Delete Methods ==== ####
    @abc.abstractmethod
    def delete(self, key):

      """ Specifies abstract version of ``Cache.delete``, which is used to
          delete an individual item from the ``Cache``.

          :param key: String key under which an item may be stored in the
            ``Cache`` that should be deleted.

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: Implementors must return the original ``key`` at which an
            item should have been deleted. """

      raise NotImplementedError('`Cache.delete`'
                                ' is abstract.')  # pragma: no cover

    @abc.abstractmethod
    def delete_multi(self, keys):

      """ Specifies abstract version of ``Cache.delete_multi``, which is used to
          delete multiple items from the ``Cache`` in one call.

          :param keys: Iterable of string keys under which existing cached items
            should be deleted.

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: Implementors must return the original iterable of ``keys``
            under which items should have been deleted. """

      raise NotImplementedError('`Cache.delete_multi`'
                                ' is abstract.')  # pragma: no cover

    @abc.abstractmethod
    def clear(self):

      """ Specifies abstract version of ``Cache.clear``, which is used to nuke
          the cache (clearing it of all items) in one call.

          :returns: ``None``, as the cache should have been nuked and what else
            would we return? """

      raise NotImplementedError('`Cache.clear`'
                                ' is abstract.')  # pragma: no cover

  class Strategy(object):

    __metaclass__ = abc.ABCMeta

    #### ==== Expiration Methods ==== ####
    @abc.abstractmethod
    def should_expire(self, key):

      """ Specifies abstract version of ``Cache.Strategy.should_expire``, which
          is called by the ``Cache`` internals on an implementing cache strategy
          to discern whether a key should be dropped from the cache.

          :param key: String key that should be evaluated against this cache
            management policy.

          :returns: Implementors are expected to return ``True`` if the key
            should expire or ``False`` if the key should be kept. """

      raise NotImplementedError('`Cache.Strategy.should_expire`'
                                ' is abstract.')  # pragma: no cover

    #### ==== Scan Methods ==== ####
    @abc.abstractmethod
    def tick(self, timestamp):

      """ Specifies abstract version of ``Cache.Strategy.tick``, which is called
          by the ``Cache`` internals every so often to trim or clean the cache.

          :param timestamp: Current integer Unix timestamp, handed-in for
            convenience.

          :returns: Nothing is expected of implementors for a return value from
            this method. """

      raise NotImplementedError('`Cache.Strategy.tick`'
                                ' is abstract.')  # pragma: no cover


@decorators.bind('cache')
class Caching(logic.Logic):

  """ Bundled logic that provides basic caching functionality through Canteen's
      builtin ``Cache`` APIs. Formerly the 'Core Cache API'. """

  #### ==== Cache Strategies ==== ####
  class PersistentCache(Cache.Strategy):

    """ Offers a ``Cache.Strategy`` designed to *never* expire keys and refuse
        to clean/trim during cache ``tick``. """

    def should_expire(self, key, timestamp):

      """ Always return ``False`` as this strategy specifies that no keys should
          be dropped, ever.

          :param key: String ``key`` to not-drop.

          :param timestamp: Integer ``timestamp`` for ``now``, as understood by
            the client. Handed in for convenience.

          :returns: ``False``. Always. """

      return False  # nope

    def tick(self, timestamp):

      """ Always return ``NotImplemented`` as a sentinel to the ``Cache``
          internals that this strategy refuses to clean/trim on cache tick.

          :returns: ``NotImplemented``. Always. """

      return NotImplemented  # double nope


  #### ==== Cache Engines ==== ####
  class Threadcache(Cache.Engine):

    """ Manages a simple thread local-backed caching engine, suitable for
        caching basic items that don't relate to HTTP state. """

    def get(self, key, default=None, _skip=False):

      """ Retrieve an item from the threadcache by key.

          :param key: Key at which an item should exist in the threadcache to
            return to the callee.

          :param default: Default item to return in the case of a nonexistent
            key. Defaults to ``None``.

          :param _skip: Internal flag that indicates we can skip checking
            ``key``'s existence, because somehow we already know it exists.

          :raises KeyError: In the case of a nonexistent ``key``, but a truthy
            value for ``_skip``, as this exposes the raw access without a
            check through ``__contains__``.

          :returns: The item cached at ``key``, if any, or ``default``. """

      if _skip or key in self.target:

        # retrieve
        value, timestamp = self.target[key]

        # dereference weakref
        if isinstance(value, weakref.ref):  # pragma: no cover
          value = value()

        # check expiration and ref and return
        if value is not None:
          if not self.strategy.should_expire(key, timestamp):
            return value
          else:  # pragma: no cover
            self.delete(key)
      return default

    def get_multi(self, keys, default=None):

      """ Retrieve multiple items at once from the threadcache by key. Basically
          a batch version of ``get``.

          :param keys: Iterable of keys to retrieve from the threadcache via
            ``get``.

          :param default: Default value to pack the resultlist with for
            nonexistent keys.

          :returns: Iterable of results for each key in ``keys``, or ``default``
            in place of items that don't exist. Order is maintained for the
            provided ``keys`` iterable. """

      return dict(((key, self.get(key, default)) for key in keys))

    def items(self):

      """ Iterate over all available keys in the cache, one by one, yielding
          them as ``(key, value)`` pairs.

          :yields: Two-item tuples of ``(key, value)`` pairs, for each ``key``
            accessible in the local ``Threadcache`` at ``self.target``. """

      for key in self.target:
        yield key, self.get(key, _skip=True)

    def set(self, key, value):

      """ Set a value in the threadcache by key.

          :param key: Key at which the value should be cached and potentially
            retrievable later.

          :param value: Value that should be stored in the cache under ``key``.
            Can be any Python-native value or value easily reducible to a raw
            Python-native value.

          :returns: Value stored in the cache. """

      value = (
        weakref.ref(value) if not isinstance(value, _BUILTIN_TYPES) else (
          value))

      self.target[key] = (value, time.time())
      return value

    def set_multi(self, map):

      """ Batch version of ``set``, defined above. Accepts a ``map`` of ``keys``
          to ``values`` which should be persisted via ``set``.

          :param map: ``dict`` or iterable of ``(key, value)`` pairs that should
            be stored in the cache.

          :returns: The fully-buffered set of items stored in the cache. """

      for key, value in (map.iteritems() if isinstance(map, dict) else map):
        self.set(key, value)
      return map

    def delete(self, key):

      """ Delete an item in the cache by ``key``.

          :param key: Key at which any matching values should be removed from
            the threadcache. """

      if key in self.target:
        del self.target[key]

    def delete_multi(self, keys):

      """ Batch version of ``delete``. Accepts an iterable of ``keys`` to delete
          from the local threadcache.

          :param keys: Iterable of keys to be deleted via ``delete``. """

      for key in keys:
        self.delete(key)

    def clear(self):

      """ Clear the entire threadcache of all values in one go.

          :returns: Number of items cleared from the threadcache. """

      length = len(self.target)
      self.target = {}
      return length

  #### ==== Internals ==== ####
  @property
  def config(self):

    """ Property accessor for caching configuration.

        :returns: Any application or framework configuration at the path
          ``Caching``. """

    from canteen.util import config  # pragma: no cover
    return config.Config().config.get('Caching', {})  # pragma: no cover

  @property
  def debug(self):  # pragma: no cover

    """ Property accessor for debug mode.

        :returns: Boolean indicating whether ``debug`` mode should be active.
          Defaults to Python's internal ``__debug__`` state. """

    return self.config.get('debug', __debug__)  # pragma: no cover

  #### ==== Cache Management ==== ####
  @staticmethod
  def spawn(name=None,
            target=None,
            engine=Threadcache,
            strategy=PersistentCache):

    """ Spawn a new cache, at name ``name``, target ``target``, and optionally
        with an ``engine``/``strategy`` pair.

        Calling ``spawn`` without any arguments returns a reference to the
        default (thread-local) ``Threadcache``, used for general state storage
        for internal operations like routing.

        :param name: Simple string name that can be used to refer to this
          particular cache. Must remain unique across caches.

        :param target: Target transport or underlying storage, if applicable.
          This is an implementation-dependent parameter, and could, for example,
          be a prebuilt memcache client object, a global variable, or a hot
          Redis connection.

        :param engine: Caching engine to use against ``target``. The engine is
          in charge of knowing how to ``set``/``get``/``delete`` items from a
          kind of caching system, such as inmemory caching or ``memcache``.

        :param strategy: Caching strategy use for the management of memory
          pressure. Default strategy is ``PersistentCache``, meaning items are
          kept for the entire lifetime of the local thread. ``Cache.Strategy``
          classes can specify methods to hook into the normal operation of
          canteen's runtime to perform items on ``tick`` or for expiration
          checks.

        :returns: Reference to the newly-spawned ``Cache`` object, prepared and
          registered with the desired ``target``/``engine``/``strategy``.  """

    global _caches
    global _default

    _localtarget, cache = _default
    if not name:
      if not cache:
        _default = _caches['__default__'] = (
          _localtarget, engine(target=_localtarget.__dict__,
                               strategy=strategy()))
      return _default[1]

    _caches[name] = engine(target=target or threading.local().__dict__,
                           strategy=strategy())
    return _caches[name]

  @staticmethod
  def clear(name=None):

    """ Clear the entire contents of a ``name``d cache. If no name is provided,
        will clear contents of *all known* caches.

        :param name: Name of the cache to clear all items from. Defaults to
          ``None``, which clears the contents of *all known* caches.

        :returns: A tuple, consisting of ``num_caches_cleared`` (a count of
          individual ``Cache`` objects cleared) and ``num_items_cleared`` (a
          full count of all items cleared from all ``Cache`` objects), in that
          order.  """

    if not name:
      _total, _cache_count = 0, 0
      for name, cache in _caches.iteritems():
        if name == '__default__':
          _localtarget, cache = cache
        _total += cache.clear()
        _cache_count += 1
      return _cache_count, _total

    if name in _caches:
      return _caches[name].clear()
    return 0, 0  # pragma: no cover

  @staticmethod
  def flush():  # pragma: no cover

    """ Perform a hard flush of the local ``_caches`` index, which should free
        all local ``Threadcache`` items and release all known connections to
        external caches.

        :returns: A tuple of wiped values for module globals ``_caches`` and
          ``_default``. """

    global _caches
    global _default

    _caches, _default = {}, (threading.local(), None)

  @classmethod
  def get(cls, key, default=None):

    """ Retrieve a key from the default cache, at the named location ``key``.

        :param key: Key at which to retrieve a value from the default cache,
          acquired via ``cls.spawn()``.

        :param default: Default value to return in the case of a missing
          ``key``. Defaults to ``None``.

        :returns: Value stored at ``key`` in the default cache, or
          ``default``. """

    return cls.spawn().get(key, default)

  @classmethod
  def get_multi(cls, keys, default=None):

    """ Batch version of ``get``, to retrieve multiple items from the default
        caching engine, acquiref via ``cls.spawn()``.

        :param keys: Iterable of ``key`` locations at which to retrieve values
          from the default ``Threadcache``.

        :param default: Default value to pad resulting list with in case items
          from ``keys`` cannot be resolved.

        :returns: ``list`` of values, synchronized with iterable ``keys`` with
          values from the default threadcache at those ``keys``, or ``default``
          in place of items that could not be found. List order is preserved
          with input.  """

    return dict(((key, cls.spawn().get(key, default)) for key in keys))

  @classmethod
  def items(cls, name=None):

    """ Iterate over all available keys in the named cache at ``name`` (or the
        default local ``Threadcache`` if no ``name`` is provided), one by one,
        yielding them as ``(key, value)`` pairs.

        :yields: Two-item tuples of ``(key, value)`` pairs, for each ``key``
          accessible in the default local ``Threadcache``. """

    for key, value in (
      cls.spawn() if name is None else cls.spawn(name)).items():
      yield key, value

  @classmethod
  def set(cls, key, value):

    """ Set a value in the default ``Threadcache``.

        :param key: Key at which to store ``value`` in the default threadlocal
          ``Threadcache``.

        :param value: Value to store at ``key`` in the default threadlocal
          ``Threadcache``.

        :returns: ``value``, as it was stored in the backing
          ``Threadcache``. """

    return cls.spawn().set(key, value)

  @classmethod
  def set_multi(cls, map):

    """ Batch version of ``set``, to apply a ``map`` of ``(key, value)`` pairs
        to the ``Threadcache``, where each ``value`` is stored at the its
        corresponding ``key`` in the default threadlocal ``Threadcache``.

        :param map: ``dict`` or iterable of ``(key, value)`` tuple pairs to
          store in the default threadlocal ``Threadcache``. """

    _cache = cls.spawn()
    for key, value in (map.iteritems() if isinstance(map, dict) else map):
      _cache.set(key, value)
    return map

  @classmethod
  def delete(cls, key):

    """ Delete an item from the default threadcache at ``key``.

        :param: ``key`` at which any matching value should immediately be
          dropped from the default threadlocal ``Threadcache``.  """

    cls.spawn().delete(key)

  @classmethod
  def delete_multi(cls, keys):

    """ Batch version of ``delete``, to delete multiple `keys`` from the default
        local ``Threadcache`` in one go.

        :param keys: Iterable of keys at which any value should be dropped
          immediately from the default local ``Threadcache`` via ``delete``. """

    _cache = cls.spawn()
    for key in keys:
      _cache.delete(key)
