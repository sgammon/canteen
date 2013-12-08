# -*- coding: utf-8 -*-

'''

  canteen: core APIs
  ~~~~~~~~~~~~~~~~~~

  contains classes that provide core functionality to Canteen-based
  apps. includes stuff like ``output``, ``transport``, ``caching``,
  ``assets`` and other important junk.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# core API
from ..meta import Proxy


class CoreAPI(object):

  '''  '''

  __owner__ = "CoreAPI"

  class __metaclass__(Proxy.Component):

    __map__ = {}  # holds map of all platform instances

    @classmethod
    def prepare(cls, target):

      '''  '''

      # resolve name, instantiate and register instance singleton
      alias = target.__binding__.__alias__ if hasattr(target, '__binding__') else target.__name__

      # if we already have a singleton, give that
      if alias in cls.__map__:
        return cls.__map__[alias]

      # otherwise, startup a new singleton
      cls.__map__[alias] = target()
      return cls.__map__[alias]



__all__ = ['CoreAPI', 'assets', 'cache', 'template']
