# -*- coding: utf-8 -*-

'''

  canteen: core cache API
  ~~~~~~~~~~~~~~~~~~~~~~~

  exposes a simple core API for caching objects in-memory or in
  caching engines like ``memcached``.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# core API & util
from . import CoreAPI
from canteen.util import decorators


@decorators.bind('cache')
class CacheAPI(CoreAPI):

  '''  '''

  pass
