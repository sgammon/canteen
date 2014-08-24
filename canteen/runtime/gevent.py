# -*- coding: utf-8 -*-

'''

  gevent runtime
  ~~~~~~~~~~~~~~

  integrates :py:mod:`canteen` with :py:mod:`gevent`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core
from ..core import runtime


with runtime.Library('gevent'):
  raise NotImplementedError('gevent is stubbed.')
