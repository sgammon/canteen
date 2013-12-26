# -*- coding: utf-8 -*-

'''

  canteen util
  ~~~~~~~~~~~~

  low-level utilities and miscellaneous tools that don't really
  belong anywhere special.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import time
import pkgutil
import datetime
import importlib


def say(*args):

  '''  '''

  print ' '.join(map(lambda x: str(x), args))


def walk(root=None, debug=True):

  '''  '''

  if debug: print 'Preloading path "%s"...' % (root or '.')
  return map((lambda x: say('Preloaded:', x)) if debug else (lambda x: x),
          map(lambda (loader, name, is_package): importlib.import_module(name).__name__ if not is_package
            else name, pkgutil.walk_packages(root or '.')))


def cacheable(key, ttl=None, expire=None):

  '''  '''

  from canteen.core.api import cache

  # process expiration
  if ttl and expire:
    raise RuntimeError('Cannot provide both a TTL and absolute expiration for cacheable item "%s".' % key)

  elif ttl and isinstance(ttl, int):
    expiration = time.time() + ttl

  elif expire and isinstance(expire, int):
    expiration = expire  # integer absolute expiration

  elif expire and isinstance(expire, datetime.datetime):
    expiration = time.mktime(expire.timetuple())

  elif (not ttl) and (not expire):
    expiration = None

  else:
    raise RuntimeError('Invalid TTL or Expire value given for cacheable item "%s".' % key)

  # make our injector and responder
  def injector(func):

    '''  '''

    def responder(*args, **kwargs):

      '''  '''

      # check expiration - flush if we have to
      if expiration and not (time.time() < expiration):

        print "Cache item expired: '%s'." % key

        cache.CacheAPI.delete(key)
        val = None
      else:
        val = cache.CacheAPI.get(key)

      # refresh the cache if we have to
      if not val:

        print "Cache miss: '%s'." % key

        val = func(*args, **kwargs)

        if val:
          cache.CacheAPI.set(key, val)

      else:
        print "Cache hit: '%s'." % key

      return val

    return responder

  return injector


__all__ = (
  'walk',
  'say',
  'cli',
  'config',
  'debug',
  'decorators',
  'struct'
)
