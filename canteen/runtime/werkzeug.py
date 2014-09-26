# -*- coding: utf-8 -*-

"""

  werkzeug runtime
  ~~~~~~~~~~~~~~~~

  runs :py:mod:`canteen`-based apps on pocoo's excellent WSGI
  library, :py:mod:`werkzeug`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib & core
import os
from ..util import struct
from ..core import runtime


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):

  # WSGI devserver
  serving, err = library.load('serving'), library.load('exceptions')

  http_exceptions = {
    'BadRequest': err.BadRequest,  # 400
    'Unauthorized': err.Unauthorized,  # 401
    'Forbidden': err.Forbidden,  # 403
    'NotFound': err.NotFound,  # 404
    'MethodNotAllowed': err.MethodNotAllowed,  # 405
    'NotAcceptable': err.NotAcceptable,  # 406
    'RequestTimeout': err.RequestTimeout,  # 408
    'Conflict': err.Conflict,  # 409
    'Gone': err.Gone,  # 410
    'LengthRequired': err.LengthRequired,  # 411
    'PreconditionFailed': err.PreconditionFailed,  # 412
    'RequestEntityTooLarge': err.RequestEntityTooLarge,  # 413
    'RequestURITooLarge': err.RequestURITooLarge,  # 414
    'UnsupportedMediaType': err.UnsupportedMediaType,  # 415
    'RequestedRangeNotSatisfiable': err.RequestedRangeNotSatisfiable,  # 416
    'ExpectationFailed': err.ExpectationFailed,  # 417
    'ImATeapot': err.ImATeapot,  # 418
    'PreconditionRequired': err.PreconditionRequired,  # 428
    'TooManyRequests': err.TooManyRequests,  # 429
    'RequestHeaderFieldsTooLarge': err.RequestHeaderFieldsTooLarge,  # 431
    'InternalServerError': err.InternalServerError,  # 500
    'NotImplemented': err.NotImplemented,  # 501
    'ServiceUnavailable': err.ServiceUnavailable,  # 502
    'ClientDisconnected': err.ClientDisconnected,
    'SecurityError': err.SecurityError}


  class Werkzeug(runtime.Runtime):

    """  """

    base_exception = err.HTTPException

    exceptions = struct.ObjectProxy(http_exceptions)

    def bind(self, interface, address):  # pragma: no cover

      """  """

      paths = {}

      # resolve static asset paths
      if 'assets' in self.config.app.get('paths', {}):
        if isinstance(self.config.app['paths'].get('assets'), dict):
          paths.update(dict((
            (k, v) for k, v in self.config.app['paths']['assets'].iteritems())))

        paths.update({
          '/assets': self.config.app['paths']['assets'],
          '/favicon.ico': self.config.app['paths'].get('favicon', False) or (
            os.path.join(self.config.app['paths']['assets'], 'favicon.ico'))})

      # append any extra asset paths
      if self.config.assets.get('config', {}).get('extra_assets'):
        paths.update((
          dict(self.config.assets['config']['extra_assets'].itervalues())))

      # run via werkzeug's awesome `run_simple`
      return serving.run_simple(interface, address, self, **{
        'use_reloader': True,
        'use_debugger': True,
        'use_evalex': True,
        'extra_files': None,
        'reloader_interval': 1,
        'threaded': True,
        'processes': 1,
        'passthrough_errors': False,
        'ssl_context': None,
        'static_files': paths})
