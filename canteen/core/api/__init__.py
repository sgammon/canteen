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
from ..meta import decorators

# core modules
from .. import meta, hooks, runtime, injection


@decorators.singleton
class CoreAPI(object):

  '''  '''

  __owner__ = "CoreAPI"
  __metaclass__ = Proxy.Component


__all__ = (
  'CoreAPI',
  'agent',
  'assets',
  'cache',
  'content',
  'session',
  'template'
)
