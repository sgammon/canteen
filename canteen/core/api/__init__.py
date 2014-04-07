# -*- coding: utf-8 -*-

'''

  canteen: core APIs
  ~~~~~~~~~~~~~~~~~~

  contains classes that provide core functionality to Canteen-based
  apps. includes stuff like ``output``, ``transport``, ``caching``,
  ``assets`` and other important junk.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core API & modules
from ..meta import Proxy, decorators
from .. import meta, hooks, runtime, injection


@decorators.singleton
class CoreAPI(object):

  '''  '''

  __owner__, __metaclass__ = "CoreAPI", Proxy.Component


__all__ = (
  'CoreAPI',
  'assets',
  'cache',
  'session',
  'template'
)
