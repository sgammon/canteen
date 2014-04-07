# -*- coding: utf-8 -*-

'''

  canteen: core cache API
  ~~~~~~~~~~~~~~~~~~~~~~~

  exposes a simple core API for caching objects in-memory or in
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

# core & util
from . import CoreAPI
from canteen.util import decorators


## Globals
_caches = {}
_default = (threading.local(), None)


class Cache(object):

  '''  '''

  class Engine(object):

    '''  '''

    target = None  # cache adapter/library
    strategy = None  # strategy to use for eviction

    __metaclass__ = abc.ABCMeta

    ## == Internals == ##
    def __init__(self, target, strategy=None):

      '''  '''

      self.target, self.strategy = target, strategy

    #### ==== Read Methods ==== ####
    @abc.abstractmethod
    def get(self, key):

      '''  '''

      raise NotImplementedError()

    @abc.abstractmethod
    def get_multi(self, keys):

      '''  '''

      raise NotImplementedError()

    @abc.abstractmethod
    def items(self, timestamp):

      '''  '''

      raise NotImplemented()

    #### ==== Write Methods ==== ####
    @abc.abstractmethod
    def set(self, key, value):

      '''  '''

      raise NotImplementedError()

    @abc.abstractmethod
    def set_multi(self, map):

      '''  '''

      raise NotImplementedError()

    #### ==== Delete Methods ==== ####
    @abc.abstractmethod
    def delete(self, key):

      '''  '''

      raise NotImplementedError()

    @abc.abstractmethod
    def delete_multi(self, keys):

      '''  '''

      raise NotImplementedError()

    @abc.abstractmethod
    def clear(self):

      '''  '''

      raise NotImplementedError()

  class Strategy(object):

    __metaclass__ = abc.ABCMeta

    #### ==== Expiration Methods ==== ####
    @abc.abstractmethod
    def should_expire(self, key):

      '''  '''

      raise NotImplemented()

    #### ==== Scan Methods ==== ####
    @abc.abstractmethod
    def tick(self, timestamp):

      '''  '''

      raise NotImplemented()


@decorators.bind('cache')
class CacheAPI(CoreAPI):

  '''  '''

  #### ==== Cache Strategies ==== ####
  class PersistentCache(Cache.Strategy):

    '''  '''

    def should_expire(self, key, tiemstamp):

      '''  '''

      return False

    def tick(self, timestamp):

      '''  '''

      return NotImplemented


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

      if not isinstance(value, (int, float, str, list, dict, tuple, unicode, type(abc))):
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

    return config.Config().config.get('CacheAPI', {})

  @property
  def debug(self):

    '''  '''

    return self.config.get('debug', True)

  #### ==== Cache Management ==== ####
  @decorators.bind(wrap=staticmethod)
  def spawn(name=None, target=None, engine=Threadcache, strategy=PersistentCache):

    '''  '''

    global _caches
    global _default

    _localtarget, cache = _default
    if not name:
      if not cache:
        _default = _caches['__default__'] = (_localtarget, engine(target=_localtarget.__dict__, strategy=strategy()))
      return _default[1]  # return engine

    _caches[name] = engine(target=target or threading.local().__dict__, strategy=strategy())
    return _caches[name]

  @decorators.bind(wrap=staticmethod)
  def clear(name=None):

    '''  '''

    if not name:
      _total, _caches = 0, 0
      for name, cache in _caches.iteritems():
        _total += cache.clear()
        _caches += 1
      return _caches, _total
    _caches[name].clear()

  @decorators.bind(wrap=staticmethod)
  def flush():

    '''  '''

    global _caches

    _caches = {}
    _default = None

    return _caches, _default

  @decorators.bind(wrap=classmethod)
  def get(cls, key):

    '''  '''

    return cls.spawn().get(key)

  @decorators.bind(wrap=classmethod)
  def get_multi(cls, keys):

    '''  '''


    _cache = cls.spawn()
    return [_cache.get(key) for key in keys]

  @decorators.bind(wrap=classmethod)
  def set(cls, key, value):

    '''  '''

    return cls.spawn().set(key, value)

  @decorators.bind(wrap=classmethod)
  def set_multi(cls, map):

    '''  '''

    _cache = cls.spawn()
    for key, value in map.iteritems():
      _cache.set(key, value)

  @decorators.bind(wrap=classmethod)
  def delete(cls, key):

    '''  '''

    return cls.spawn().delete(key)

  @decorators.bind(wrap=classmethod)
  def delete_multi(cls, keys):

    '''  '''

    _cache = cls.spawn()
    for key in keys:
      _cache.delete(key)


__all__ = (
  'Cache',
  'CacheAPI'
)
