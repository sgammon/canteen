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

# stdlib & core
import os
from ..core import runtime


with runtime.Library('werkzeug') as (library, werkzeug):

  # WSGI devserver
  serving = library.load('serving')


  class Werkzeug(runtime.Runtime):

    '''  '''

    def bind(self, interface, address):

      '''  '''

      # resolve static asset paths
      if 'assets' in self.config.app.get('paths', {}):
        if isinstance(self.config.app['paths'].get('assets'), dict):
          paths = dict(((k, v) for k, v in self.config.app['paths']['assets'].iteritems()))
        paths = {
          '/assets': self.config.app['paths']['assets'],
          '/favicon.ico': self.config.app['paths'].get('favicon', False) or os.path.join(
            self.config.app['paths']['assets'],
            'favicon.ico'
        )}

      # run via werkzeug's awesome `run_simple`
      return serving.run_simple(interface, address, self.dispatch, **{
        'use_reloader': True,
        'use_debugger': True,
        'use_evalex': True,
        'extra_files': None,
        'reloader_interval': 1,
        'threaded': False,
        'processes': 1,
        'passthrough_errors': False,
        'ssl_context': self.config.app.get('ssl', {}).get('certificate', 'adhoc'),
        'static_files': paths
      })
