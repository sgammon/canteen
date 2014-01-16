# -*- coding: utf-8 -*-

'''

  canteen uwsgi runtime
  ~~~~~~~~~~~~~~~~~~~~~

  integrates :py:mod:`canteen` with :py:mod:`uwsgi`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core
from ..core import runtime


with runtime.Library('uwsgi'):
  raise NotImplementedError('uwsgi is stubbed.')


  __all__ = tuple()
