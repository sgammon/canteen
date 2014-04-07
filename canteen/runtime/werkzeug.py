# -*- coding: utf-8 -*-

'''

  canteen: werkzeug runtime
  ~~~~~~~~~~~~~~~~~~~~~~~~~

  runs :py:mod:`canteen`-based apps on pocoo's excellent WSGI
  library, :py:mod:`werkzeug`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib & core
import os
from ..util import struct
from ..core import runtime


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):

  # WSGI devserver
  serving, exceptions = library.load('serving'), library.load('exceptions')


  class Werkzeug(runtime.Runtime):

    '''  '''

    base_exception = exceptions.HTTPException

    exceptions = struct.ObjectProxy({
      'BadRequest': exceptions.BadRequest,  # 400
      'Unauthorized': exceptions.Unauthorized,  # 401
      'Forbidden': exceptions.Forbidden,  # 403
      'NotFound': exceptions.NotFound,  # 404
      'MethodNotAllowed': exceptions.MethodNotAllowed,  # 405
      'NotAcceptable': exceptions.NotAcceptable,  # 406
      'RequestTimeout': exceptions.RequestTimeout,  # 408
      'Conflict': exceptions.Conflict,  # 409
      'Gone': exceptions.Gone,  # 410
      'LengthRequired': exceptions.LengthRequired,  # 411
      'PreconditionFailed': exceptions.PreconditionFailed,  # 412
      'RequestEntityTooLarge': exceptions.RequestEntityTooLarge,  # 413
      'RequestURITooLarge': exceptions.RequestURITooLarge,  # 414
      'UnsupportedMediaType': exceptions.UnsupportedMediaType,  # 415
      'RequestedRangeNotSatisfiable': exceptions.RequestedRangeNotSatisfiable,  # 416
      'ExpectationFailed': exceptions.ExpectationFailed,  # 417
      'ImATeapot': exceptions.ImATeapot,  # 418
      'PreconditionRequired': exceptions.PreconditionRequired,  # 428
      'TooManyRequests': exceptions.TooManyRequests,  # 429
      'RequestHeaderFieldsTooLarge': exceptions.RequestHeaderFieldsTooLarge,  # 431
      'InternalServerError': exceptions.InternalServerError,  # 500
      'NotImplemented': exceptions.NotImplemented,  # 501
      'ServiceUnavailable': exceptions.ServiceUnavailable,  # 502
      'ClientDisconnected': exceptions.ClientDisconnected,
      'SecurityError': exceptions.SecurityError
    })

    def bind(self, interface, address):

      '''  '''

      paths = {}

      # resolve static asset paths
      if 'assets' in self.config.app.get('paths', {}):
        if isinstance(self.config.app['paths'].get('assets'), dict):
          paths.update(dict(((k, v) for k, v in self.config.app['paths']['assets'].iteritems())))

        paths.update({
          '/assets': self.config.app['paths']['assets'],
          '/favicon.ico': self.config.app['paths'].get('favicon', False) or os.path.join(
            self.config.app['paths']['assets'],
            'favicon.ico'
        )})

      # append any extra asset paths
      if self.config.assets.get('config', {}).get('extra_assets'):
        paths.update(dict(self.config.assets['config']['extra_assets'].itervalues()))

      # run via werkzeug's awesome `run_simple`
      return serving.run_simple(interface, address, self, **{
        'use_reloader': True,
        'use_debugger': True,
        'use_evalex': True,
        'extra_files': None,
        'reloader_interval': 1,
        'threaded': False,
        'processes': 1,
        'passthrough_errors': False,
        'ssl_context': None,
        'static_files': paths
      })


  __all__ = ('Werkzeug',)
