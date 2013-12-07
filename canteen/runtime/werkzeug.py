# -*- coding: utf-8 -*-

'''

  canteen werkzeug runtime
  ~~~~~~~~~~~~~~~~~~~~~~~~

  runs :py:mod:`canteen`-based apps on pocoo's excellent WSGI
  library, :py:mod:`werkzeug`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import importlib

# core
from ..core import runtime


with runtime.Library('werkzeug') as (library, werkzeug):

  # WSGI devserver
  serving = library.load('serving')


  class Werkzeug(runtime.Runtime):

    '''  '''

    def bind(self, interface, address):

      '''  '''

      return serving.run_simple(interface, address, self.dispatch, **{
        'use_reloader': True,
        'use_debugger': False,
        'use_evalex': True,
        'extra_files': None,
        'reloader_interval': 1,
        'threaded': True,
        'processes': 1,
        'static_files': None,
        'passthrough_errors': False,
        'ssl_context': None
      })
