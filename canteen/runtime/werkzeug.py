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
import sys, os, socket
import subprocess, signal

# canteen
from ..util import walk
from ..util import struct
from ..core import runtime


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):

  # defaults
  default_config = {

    ## Code Reloader
    'reloader': {
      'enabled': False,
      'interval': 5
    },

    ## Integrated Debugger
    'debugger': {
      'enabled': False,
      'use_evalex': True
    }

  }

  # WSGI, serving and debug tools
  wsgi, serving, exceptions, debug = (
    library.load('wsgi'),
    library.load('serving'),
    library.load('exceptions'),
    library.load('debug') if __debug__ else None,
  )


  class Werkzeug(runtime.Runtime):

    '''  '''

    middleware = None
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

    def add_wrap(self, target, *args, **kwargs):

      '''  '''

      if not self.middleware: self.middleware = []
      self.middleware.append((target, args, kwargs))
      return self.middleware

    def wrap(self, dispatch):

      '''  '''

      for wrap, args, kwargs in self.middleware:  # apply added middleware
        dispatch = wrap(dispatch, *args, **kwargs)
      return super(Werkzeug, self).wrap(dispatch)  # pass up the chain

    def bind(self, interface, port):

      '''  '''

      paths, do_bind = {}, None

      # sanity checks
      assert 1 < port < 65534, "please provide a valid port (range 1 - 65534)"

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

      # if we want to run the debugger, attach it
      if __debug__ and self.config.get('werkzeug', {}).get('debugger', False):
        if (isinstance(self.config.config['werkzeug']['debugger'], dict) and self.config.config['werkzeug']['debugger'].get('enabled', False)):
          self.add_wrap(debug.DebuggedApplication, self.config.config['werkzeug']['debugger'].get('use_evalex', True))
        elif self.config.config['werkzeug']['debugger']:
          self.add_wrap(debug.DebuggedApplication)

      # if we have statics to serve, do it through shared data
      if paths: self.add_wrap(wsgi.SharedDataMiddleware, paths)

      # if we want to use the reloader, set it up
      if __debug__ and self.config.get('werkzeug', {}).get('reloader', False):

        do_reloader, reloader_cfg = True, {}
        if isinstance(self.config.config['werkzeug']['reloader'], dict):
          if self.config.config['werkzeug']['reloader']['enabled']:
            do_reloader, reloader_cfg = True, self.config.config['werkzeug']['reloader']
          else:
            do_reloader = False

        if do_reloader:
          def do_bind(*args, **kwargs):

            '''  '''

            def do_inner():

              import socket, thread

              try:
                if args or kwargs:
                  server_factory(*args, **kwargs)
                server_factory()
              except Exception as e:
                thread.exit()

            try:
              serving.run_with_reloader(do_inner, paths or None, reloader_cfg.get('interval', 5))

            except (SystemExit, KeyboardInterrupt) as e:
              if e.code != 3: sys.exit(e.code)
              runtime.Runtime.respawn()

            except BaseException as e:
              import traceback
              traceback.print_exception(*sys.exc_info())
              print 'Fatal exception. Exiting.'
              sys.exit(e.code)

      # if we don't have one yet, setup default server init
      if not do_bind:
        def do_bind(): return server_factory()

      processes, threads = (
        self.config.get('werkzeug', {}).get('serving', {}).get('processes', 1),
        self.config.get('werkzeug', {}).get('serving', {}).get('threads', None)
      )

      # pick a server factory
      if processes > 1 and threads: raise RuntimeError('Multithreaded multiprocess serving is not yet supported.')
      if not 0 < processes < 25: raise RuntimeError('Please pick a sane number of threads (say, less than 25 and more than 0).')
      if processes == 1 and not threads: server_target = serving.BaseWSGIServer
      if processes > 1 and not threads: server_target = serving.ForkingWSGIServer
      if processes == 1 and threads: server_target = serving.ThreadedWSGIServer

      def server_factory(*args, **kwargs):
        return server_target(*args, **kwargs).serve_forever()

      # resolve hostname
      hostname = self.config.get('werkzeug', {}).get('serving', {}).get('hostname', 'localhost')

      ## stolen from werkzeug: spawn a socket to force any related exceptions before proc spawn
      address_family = serving.select_ip_version(hostname, port)
      test_socket = socket.socket(address_family, socket.SOCK_STREAM)
      test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      test_socket.bind((hostname, port))
      test_socket.close()

      return do_bind(hostname, port, self)  # start the server and serve forever!


  __all__ = ('Werkzeug',)
