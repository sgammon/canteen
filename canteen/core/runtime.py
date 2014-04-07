# -*- coding: utf-8 -*-

'''

  canteen: runtime core
  ~~~~~~~~~~~~~~~~~~~~~

  platform internals and logic to discover/load/inject.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os
import sys
import abc
import time
import inspect
import importlib

# core API
from .meta import Proxy
from .injection import Bridge


class Runtime(object):

  '''  '''

  # == Public Properties == #

  routes = None  # compiled route map
  config = None  # application config
  bridge = None  # window into the injection pool
  application = None  # WSGI application callable or delegate

  # == Private Properties == #
  __hooks__ = {}  # mapped hookpoints and methods to call
  __owner__ = "Runtime"  # metabucket owner name for subclasses
  __wrapped__ = None  # wrapped dispatch method calculated on first request
  __singleton__ = False  # many runtimes can exist, _so power_
  __metaclass__ = Proxy.Component  # this should be injectable

  # == Abstract Properties == #
  @abc.abstractproperty
  def base_exception(self):

    '''  '''

    return False

  @classmethod
  def spawn(cls, app):

    '''  '''

    return (cls.resolve() if cls is Runtime else cls)(app)  # if we're running as ``Runtime``, resolve a runtime first

  @classmethod
  def resolve(cls):

    '''  '''

    # @TODO(sgammon): figure out how to prioritize/select a runtime
    _default, _preferred = None, []
    for child in cls.iter_children():
      if hasattr(child, '__default__') and child.__default__:
        _default = child
        continue
      _preferred.append(child)

    if _preferred:
      return _preferred[0]  # Werkzeug
    return _default  # WSGIref

  @classmethod
  def add_hook(cls, hook, (context, func)):

    '''  '''

    assert isinstance(hook, basestring), "hook name must be a string"
    if hook not in cls.__hooks__: cls.__hooks__[hook] = []
    cls.__hooks__[hook].append((context, func))
    return cls

  @classmethod
  def get_hooks(cls, point):

    '''  '''

    if point in cls.__hooks__:
      for i in cls.__hooks__[point]:
        yield i
    raise StopIteration()

  @classmethod
  def execute_hooks(cls, points, *args, **kwargs):

    '''  '''

    if isinstance(points, basestring): points = (points,)
    for point in points:
      for context, hook in cls.get_hooks(point):
        try:
          # run as classmethod
          if isinstance(hook, classmethod):
            hook.__func__(context, *args, **kwargs)

          # run as staticmethod
          elif isinstance(hook, staticmethod):
            hook.__func__(*args, **kwargs)

          else:

            # must have a singleton if we're running in object context
            if not hasattr(context, '__singleton__') or not context.__singleton__:
              raise RuntimeError('Cannot execute hook method "%s" without matching singleton context.' % hook)

            # resolve singleton by context name
            obj = Proxy.Component.singleton_map.get(context.__name__)
            if not obj: raise RuntimeError('No matching singleton for hook method "%s".' % hook)

            # run in singleton context
            hook(point, obj, *args, **kwargs)

        except Exception as e:
          if __debug__:
            raise

    return

  def __init__(self, app):

    '''  '''

    self.application, self.bridge = (
      app,
      Bridge()
    )

  def initialize(self):

    '''  '''

    self.execute_hooks('initialize', runtime=self)

  def configure(self, config):

    '''  '''

    self.config = config
    self.initialize()  # let subclasses initialize
    return self

  def serve(self, interface, port, bind_only=False):

    '''  '''

    server = self.bind(interface, port)

    if bind_only:
      return server

    try:
      server.serve_forever()
    except (KeyboardInterrupt, Exception) as e:
      print "Exiting."
      sys.exit(0)

  def bind_environ(self, environ):

    '''  '''

    from ..logic import http
    self.routes = http.HTTPSemantics.route_map.bind_to_environ(environ)

    return (
      http.HTTPSemantics,
      http.HTTPSemantics.new_request(environ),
      http.HTTPSemantics.new_response()
    )

  def dispatch(self, environ, start_response):

    '''  '''

    from ..base import handler as base_handler

    # setup hook context
    context = {
      'environ': environ,
      'start_response': start_response,
      'runtime': self
    }

    # call dispatch hooks
    self.execute_hooks('dispatch', **context)

    # resolve URL via bound routes
    http, request, response = (
      context['http'],
      context['request'],
      context['response']
    ) = self.bind_environ(environ)

    # call request hooks
    self.execute_hooks('request', **context)

    # match route
    endpoint, arguments = (
      context['endpoint'],
      context['arguments']
    ) = self.routes.match()

    # call match hooks
    self.execute_hooks('match', **context)

    # resolve endpoint
    handler = context['handler'] = http.resolve_route(endpoint)

    if not handler:  # `None` for handler means it didn't match

      # update context
      context.update({
        'code': 404,
        'error': True,
        'exception': None,
        'response': None
      })

      # dispatch error hook for 404
      self.execute_hooks(('error', 'complete'), **context)
      http.error(404)

    # class-based pages/handlers
    if isinstance(handler, type) and issubclass(handler, base_handler.Handler):

      # initialize handler
      flow = context['handler'] = handler(**context)

      # call handler hooks
      self.execute_hooks('handler', **context)

      # dispatch time: INCEPTION.
      result, iterator = flow(arguments), None

      if isinstance(result, tuple) and len(result) == 2:
        iterator, result = result  # extract iterator and raw result

      elif isinstance(result, tuple) and len(result) == 4:

        status, headers, content_type, content = (
          context['status'],
          context['headers'],
          context['content_type'],
          context['content']
        ) = result  # unpack response

        _response = context['response'] = response.__class__(content, **{
          'status': status,
          'headers': headers,
          'mimetype': content_type
        })

        # call response hooks
        self.execute_hooks(('response', 'complete'), **context)
        return _response(environ, start_response)

      status, headers, content_type, content = (
        context['status'],
        context['headers'],
        context['content_type'],
        context['content']
      ) = result.status, result.headers, result.content_type, result.response  # unpack response

      # call response hooks
      self.execute_hooks(('response', 'complete'), **context)

      # send start_response
      start_response(result.status, [(k.encode('utf-8').strip(), v.encode('utf-8').strip()) for k, v in result.headers])

      # buffer and return (i guess) @TODO(sgammon): can we do this better?
      return iterator or result.response  # it's a werkzeug Response

    # delegated class-based handlers (for instance, other WSGI apps)
    elif isinstance(handler, type) or callable(handler):

      # make a neat little shim, containing our runtime
      def _foreign_runtime_bridge(status, headers):

        '''  '''

        # call response hooks
        context['status'], context['headers'], context['response'] = (
          status,
          headers,
          None
        )

        self.execute_hooks(('response', 'complete'), **context)
        return start_response(status, headers)

      # attach runtime, arguments and actual start_response to shim
      _foreign_runtime_bridge.runtime = self
      _foreign_runtime_bridge.arguments = arguments
      _foreign_runtime_bridge.start_response = start_response
      context['start_response'] = _foreign_runtime_bridge

      # call handler hooks, initialize foreign handler with replaced start_response
      self.execute_hooks('handler', **context)
      return handler(environ, _foreign_runtime_bridge)

    # is it a function, maybe?
    if inspect.isfunction(handler):

      # inject stuff into context
      for prop, val in (
        ('runtime', self),
        ('self', self.bridge),
        ('arguments', arguments),
        ('request', request),
        ('response', response),
        ('environ', environ),
        ('start_response', start_response),
        ('Response', response.__class__)):

        handler.__globals__[prop] = val  # inject all the things

      # call handler hooks
      self.execute_hooks('handler', **context)

      # call with arguments only
      result = context['response'] = handler(**arguments)

      if isinstance(result, response.__class__):

        # call response hooks
        context['headers'], context['content'] = (
          result.headers, result.response
        )

        self.execute_hooks(('response', 'complete'), **context)
        return response(environ, start_response)  # it's a Response class - call it to start_response

      # a tuple bound to a URL - static response
      elif isinstance(result, tuple):

        if len(result) == 2:  # it's (status_code, response)
          status, response = (
            context['status'],
            context['response'],
          ) = result

          headers = context['headers'] = [
            ('Content-Type', 'text/html; charset=utf-8')
          ]

          # call response hooks
          self.execute_hooks(('response', 'complete'), **context)
          start_response(status, headers)
          return iter([response])

        if len(result) == 3:  # it's (status_code, headers, response)
          status, headers, response = (
            context['status'],
            context['headers'],
            context['response']
          ) = result

          if isinstance(headers, dict):
            headers = headers.items()
            if 'Content-Type' not in headers:
              headers['Content-Type'] = context['headers']['Content-Type'] = 'text/html; charset=utf-8'

          # call response hooks
          self.execute_hooks(('response', 'complete'), **context)
          start_response(status, headers)
          return iter([response])

      elif isinstance(result, basestring):

        status, headers = (
          context['status'],
          context['headers'],
          context['response']
        ) = '200 OK', [('Content-Type', 'text/html; charset=utf-8')], result

        # call response hooks
        self.execute_hooks(('response', 'complete'), **context)
        start_response(status, headers)
        return iter([result])

    # could be a bound response
    if not callable(handler):
      if isinstance(handler, basestring):

        status, headers = (
          context['status'],
          context['headers'],
          context['response']
        ) = '200 OK', [('Content-Type', 'text/html; charset=utf-8')], handler

        # call response hooks
        self.execute_hooks(('response', 'complete'), **context)
        return iter([handler])  # it's a static response!

    raise RuntimeError('Unrecognized handler type: "%s".' % type(handler))

  def wrap(self, dispatch):

    '''  '''

    if not self.__wrapped__:

      # default: return dispatch directly
      _dispatch = dispatch

      # == development wrappers
      dev_config = getattr(self.config, 'app', {}).get('dev', {})

      # profiler support
      if 'profiler' in dev_config:
        if dev_config['profiler'].get('enable', False):

          ## grab a profiler
          try:
            import cProfile as profile
          except ImportError as e:
            import profile

          ## calculate dump file path
          profile_path = dev_config['profiler'].get('dump_file', os.path.abspath(os.path.join(os.getcwd(), '.develop', 'app.profile')))

          ## current profile
          _current_profile = profile.Profile(**dev_config['profiler'].get('profile_kwargs', {}))

          ## handle flushing mechanics
          if dev_config['profiler'].get('on_request', True):

            def maybe_flush_profile():

              '''  '''

              _current_profile.dump_stats(profile_path)

          else:
            raise RuntimeError('Cross-request profiling is currently unsupported.')  # @TODO(sgammon): cross-request profiling

          def _dispatch(*args, **kwargs):

            ''' Wrapper to enable profiler support. '''

            ## dispatch
            response = _current_profile.runcall(dispatch, *args, **kwargs)
            maybe_flush_profile()
            return response

      self.__wrapped__ = _dispatch  # cache locally

    return self.__wrapped__

  @abc.abstractmethod
  def bind(self, interface, address):

    '''  '''

    raise NotImplementedError

  def __call__(self, environ, start_response):

    '''  '''

    try:
      return self.wrap(self.dispatch)(environ, start_response)

    except self.base_exception as exc:
      return exc(environ, start_response)  # it's an acceptable exception that can be returned as a response

    except Exception:
      raise  # just raise it k?


class Library(object):

  '''  '''

  name = None  # string name of the library
  strict = False  # whether to hard-fail on ImportError
  package = None  # reference to the actual library package/module
  exception = None  # captured ImportError or AttributeError exception, if any
  supported = None  # boolean flag indicating whether this lib is supported or not

  __owner__, __metaclass__ = "Library", Proxy.Component

  def __init__(self, package, strict=False):

    '''  '''

    if isinstance(package, basestring):
      self.name = package
    elif isinstance(package, type(abc)):
      self.name, self.package, self.supported = package.__name__, package, True
    self.strict = strict

  def load(self, *subpackages):

    '''  '''

    loaded = []
    for package in subpackages:
      loaded.append(importlib.import_module('.'.join((self.name, package))))
    if len(loaded) == 1:
      return loaded[0]  # special case: one package only (return it directly)
    return tuple(loaded)  # otherwise, return a tuple of loaded modules

  def __enter__(self):

    '''  '''

    if not self.package and (self.supported is None):
      try:
        self.package = importlib.import_module(self.name)
      except ImportError as e:
        self.supported, self.exception = False, e
        if self.strict:
          raise
      else:
        self.supported = True
    return (self, self.package)

  def __exit__(self, exception_cls, exception, traceback):

    '''  '''

    if exception:
      if self.strict: return False

    return True


__all__ = (
  'Runtime',
  'Library'
)
