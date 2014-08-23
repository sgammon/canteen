# -*- coding: utf-8 -*-

'''

  caching logic
  ~~~~~~~~~~~~~

  exposes simple logic for caching objects in-memory or in
  caching engines like ``memcached``.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

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

  ''' Specifies an instance of a cache, that supports
      storage and retrieval of arbitrary native Python
      values.

      Attached to every :py:class:`Cache` is a ``Strategy``
      and a ``Target``, specifying the management policy
      and underlying caching engine, respectively.

      Both components are extendable to create custom
      caching solutions. '''

  class Engine(object):

    '''  '''

    target = None  # cache adapter/library
    strategy = None  # strategy to use for eviction

    __metaclass__ = abc.ABCMeta

    ## == Internals == ##
    def __init__(self, target, strategy=None):

      ''' Initialize a new ``Cache``, utilizing
          ``target`` as a cache adapter/library
          ``strategy`` as a cache management
          policy.

          :param target: Target library or cache
          system.

          :param strategy: Cache management
          policy, extending ``Cache.Strategy``. '''

      self.target, self.strategy = target, strategy

    #### ==== Read Methods ==== ####
    @abc.abstractmethod
    def get(self, key):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.get``,
          which is used to retrieve cached items.

          :param key: Cached item's key.

          :raises NotImplementedError: Always, as this
          method is abstract.

          :returns: Implementors must return the cached
          item stored at ``key``. '''

      raise NotImplementedError('`Cache.get` is abstract.')

    @abc.abstractmethod
    def get_multi(self, keys):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.get_multi`,
          which is used to retrieve multiple cache items
          ine one call.

          :param keys: Iterable of cached item keys.

          :raises NotImplementedError: Always, as this
          method is abstract.

          :returns: Implementors must return an iterable of
          cached items, or ``None``, according to that
          result's position in the original ``keys`` iterable. '''

      raise NotImplementedError('`Cache.get_multi` is abstract.')

    @abc.abstractmethod
    def items(self, timestamp):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.items``,
          which is used to iterate over items in the
          cache, optionally current to ``timestamp``.

          This method is optional for implementors but
          must always be defined. If an implementing
          class wishes not to implement this method,
          it must return ``NotImplemented``.

          :param timestamp: Optionally only return
          cached items that were saved after the
          given ``datetime.datetime`` or integer
          Unix timestamp.

          :raises NotImplementedError: Always, as this
          method is abstract.

          :returns: Implementors must either return
          ``NotImplemented`` (if they choose not to
          provide an ``items`` implementation) or an
          iterator that will yield ``(key, value)``
          tuples of items in the cache, optionally
          current to ``timestamp``. '''

      raise NotImplementedError('`Cache.items` is abstract.')

    #### ==== Write Methods ==== ####
    @abc.abstractmethod
    def set(self, key, value):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.set``,
          which is used to store individual items in
          the ``Cache``.

          :param key: String key the item should be
          stored at, for future reference.

          :param value: Raw value to be stored in the
          cache at ``key``.

          :raises NotImplementedError: Always, as this
          method is abstract.

          :returns: Implementors must return the original
          value passed in to be cached at ``value``. '''

      raise NotImplementedError('`Cache.set` is abstract.')

    @abc.abstractmethod
    def set_multi(self, map):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.set_multi``,
          which is used to write multiple items to the
          ``Cache`` in one call.

          :param map: Iterable of ``(key, value)`` tuples
          or ``dict`` of ``key=>value`` mappings that should
          be saved to the cache.

          :raises NotImplementedError: Always, as this
          method is abstract.

          :returns: Implementors must return the original
          iterable or ``dict`` of values passed in to be
          cached at ``map``. '''

      raise NotImplementedError('`Cache.set_multi` is abstract.')

    #### ==== Delete Methods ==== ####
    @abc.abstractmethod
    def delete(self, key):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.delete``,
          which is used to delete an individual item from
          the ``Cache``.

          :param key: String key under which an item may be
          stored in the ``Cache`` that should be deleted.

          :raises NotImplementedError: Always, as this
          method is abstract.

          :returns: Implementors must return the original
          ``key`` at which an item should have been deleted. '''

      raise NotImplementedError('`Cache.delete` is abstract.')

    @abc.abstractmethod
    def delete_multi(self, keys):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.delete_multi``,
          which is used to delete multiple items from the
          ``Cache`` in one call.

          :param keys: Iterable of string keys under which
          existing cached items should be deleted.

          :raises NotImplementedError: Always, as this
          method is abstract.

          :returns: Implementors must return the original
          iterable of ``keys`` under which items should have
          been deleted. '''

      raise NotImplementedError('`Cache.delete_multi` is abstract.')

    @abc.abstractmethod
    def clear(self):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.clear``, which
          is used to nuke the cache (clearing it of all items)
          in one call.

          :returns: ``None``, as the cache should have been
          nuked and what else would we return? '''

      raise NotImplementedError('`Cache.clear` is abstract.')

  class Strategy(object):

    __metaclass__ = abc.ABCMeta

    #### ==== Expiration Methods ==== ####
    @abc.abstractmethod
    def should_expire(self, key):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.Strategy.should_expire``,
          which is called by the ``Cache`` internals on an implementing
          cache strategy to discern whether a key should be dropped from
          the cache.

          :param key: String key that should be evaluated against this
          cache management policy.

          :returns: Implementors are expected to return ``True`` if the
          key should expire or ``False`` if the key should be kept. '''

      raise NotImplementedError('`Cache.Strategy.should_expire` is abstract.')

    #### ==== Scan Methods ==== ####
    @abc.abstractmethod
    def tick(self, timestamp):  # pragma: no cover

      ''' Specifies abstract version of ``Cache.Strategy.tick``, which
          is called by the ``Cache`` internals every so often to trim
          or clean the cache.

          :param timestamp: Current integer Unix timestamp, handed-in
          for convenience.

          :returns: Nothing is expected of implementors for a return
          value from this method. '''

      raise NotImplementedError('`Cache.Strategy.tick` is abstract.')


@decorators.bind('cache')
class Caching(logic.Logic):

  ''' Bundled logic that provides basic caching functionality
      through Canteen's builtin ``Cache`` APIs. Formerly the
      'Core Cache API'. '''

  #### ==== Cache Strategies ==== ####
  class PersistentCache(Cache.Strategy):

    ''' Offers a ``Cache.Strategy`` designed to *never* expire
        keys and refuse to clean/trim during cache ``tick``. '''

    def should_expire(self, key, timestamp):  # pragma: no cover

      ''' Always return ``False`` as this strategy specifies
          that no keys should be dropped, ever.

          :param key: String ``key`` to not-drop.
          :param timestamp: Integer ``timestamp`` for ``now``,
          as understood by the client. Handed in for convenience.

          :returns: ``False``. Always. '''

      return False  # nope

    def tick(self, timestamp):  # pragma: no cover

      ''' Always return ``NotImplemented`` as a sentinel to
          the ``Cache`` internals that this strategy refuses
          to clean/trim on cache tick.

          :returns: ``NotImplemented``. Always. '''

      return NotImplemented  # double nope


  #### ==== Cache Engines ==== ####
  class Threadcache(Cache.Engine):

    '''  '''

    def get(self, key, default=None):

      '''  '''

      if key in self.target:

        # retrieve
        value, timestamp = self.target[key]

        # dereference weakref
        if isinstance(value, weakref.ref):
          value = value()

        # check expiration and ref and return
        if value is not None:
          if not self.strategy.should_expire(key, timestamp):
            return value
          self.delete(key)
      return default

    def get_multi(self, keys, default=None):

      '''  '''

      return [self.get(key) for key in keys]

    def items(self):

      '''  '''

      for key in self.target:
        yield key, self.get(key)

    def set(self, key, value):

      '''  '''

      if not isinstance(value, _BUILTIN_TYPES):
        value = weakref.ref(value)
      self.target[key] = (value, time.time())
      return value

    def set_multi(self, map):

      '''  '''

      for key, value in map.iteritems():
        self.set(key, value)
      return map

    def delete(self, key):

      '''  '''

      if key in self.target:
        del self.target[key]

    def delete_multi(self, keys):

      '''  '''

      for key in keys:
        self.delete(key)

    def clear(self):

      '''  '''

      length = len(self.target)
      self.target = {}
      return length

  #### ==== Internals ==== ####
  @property
  def config(self):

    '''  '''

    from canteen.util import config
    return config.Config().config.get('Caching', {})

  @property
  def debug(self):

    '''  '''

    return self.config.get('debug', True)

  #### ==== Cache Management ==== ####
  @staticmethod
  def spawn(name=None,
            target=None,
            engine=Threadcache,
            strategy=PersistentCache):

    '''  '''

    global _caches
    global _default

    _localtarget, cache = _default
    if not name:
      if not cache:
        _default = _caches['__default__'] = (
          _localtarget, engine(target=_localtarget.__dict__,
                               strategy=strategy()))
      return _default[1]  # return engine

    _caches[name] = engine(target=target or threading.local().__dict__,
                           strategy=strategy())
    return _caches[name]

  @staticmethod
  def clear(name=None):

    '''  '''

    if not name:
      _total, _caches = 0, 0
      for name, cache in _caches.iteritems():
        _total += cache.clear()
        _caches += 1
      return _caches, _total
    _caches[name].clear()

  @staticmethod
  def flush():

    '''  '''

    global _caches

    _caches = {}
    _default = None

    return _caches, _default

  @classmethod
  def get(cls, key):

    '''  '''

    return cls.spawn().get(key)

  @classmethod
  def get_multi(cls, keys):

    '''  '''


    _cache = cls.spawn()
    return [_cache.get(key) for key in keys]

  @classmethod
  def set(cls, key, value):

    '''  '''

    return cls.spawn().set(key, value)

  @classmethod
  def set_multi(cls, map):

    '''  '''

    _cache = cls.spawn()
    for key, value in map.iteritems():
      _cache.set(key, value)

  @classmethod
  def delete(cls, key):

    '''  '''

    return cls.spawn().delete(key)

  @classmethod
  def delete_multi(cls, keys):

    '''  '''

    _cache = cls.spawn()
    for key in keys:
      _cache.delete(key)


__all__ = (
  'Cache',
  'Caching'
)
