# -*- coding: utf-8 -*-

'''

  canteen platform core
  ~~~~~~~~~~~~~~~~~~~~~

  platform internals and logic to discover/load/inject.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# core API
from .meta import Proxy


class Platform(object):

  '''  '''

  __owner__, __metaclass__ = "Platform", Proxy.Component
