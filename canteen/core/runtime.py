# -*- coding: utf-8 -*-

"""

  core runtime
  ~~~~~~~~~~~~

  platform internals and logic to discover/load/inject.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

from __future__ import print_function

# stdlib
import os
import sys
import abc
import inspect
import importlib
import threading

# core API
from .meta import Proxy
from .injection import Bridge


## Globals
__runtime__ = threading.local()


class Runtime(object):

  """ Describes a structure that can manage and schedule execution for Canteen
      applications. When a Canteen app is running, there is always an active
      ``Runtime`` object behind it.

      One ``Runtime`` is active per thread at-at-time. It is not possible to use
      different ``Runtime`` classes concurrently (for instance, uWSGI and PyPy),
      but runtimes can be composed into a compound structure that expresses
      combined functionality. """

  # == Public Properties == #

  routes = None  # compiled route map
  config = None  # application config
  bridge = None  # window into the injection pool
  application = None  # WSGI application callable or delegate

  # == Private Properties == #
  __hooks__ = {}  # mapped hook points and methods to call
  __owner__ = "Runtime"  # meta bucket owner name for subclasses
  __wrapped__ = None  # wrapped dispatch method calculated on first request
  __singleton__ = False  # many runtimes can exist, _so power_
  __metaclass__ = Proxy.Component  # this should be injectable
  __precedence__ = False  # marked if a specific runtime should win in selection
  precedence = property(lambda self: self.__precedence__)  # protect writes

  # == Abstract Properties == #
  @staticmethod
  def base_exception():

    """  """

    return False

  @classmethod
  def spawn(cls, app):

    """  """

    global __runtime__
    if not getattr(__runtime__, 'active', None):
      __runtime__.active = (cls.resolve() if cls is Runtime else cls)(app)
    return __runtime__.active

  @classmethod
  def resolve(cls):

    """  """

    # @TODO(sgammon): figure out how to prioritize/select a runtime
    _default, _preferred = None, []
    for child in cls.iter_children():
      if hasattr(child, '__default__') and child.__default__:
        _default = child
        continue
      _preferred.append(child)

    for item in _preferred:
      if item.__precedence__:
        return item  # usually uWSGI
    if _preferred:
      return _preferred[0]  # Werkzeug
    return _default  # WSGIref

  @classmethod
  def set_precedence(cls, status=False):

    """  """

    return setattr(cls, '__precendence__', status) or cls

  @classmethod
  def add_hook(cls, hook, context_and_func):

    """  """

    context, func = context_and_func
    assert isinstance(hook, basestring), "hook name must be a string"
    if hook not in cls.__hooks__: cls.__hooks__[hook] = []
    cls.__hooks__[hook].append((context, func))
    return cls

  @classmethod
  def get_hooks(cls, point):

    """  """

    if point in cls.__hooks__:
      for i in cls.__hooks__[point]:
        yield i
    raise StopIteration()

  @classmethod
  def execute_hooks(cls, points, *args, **kwargs):

    """  """

    if isinstance(points, basestring): points = (points,)
    for point in points:
      for context, hook in cls.get_hooks(point):
        # noinspection PyBroadException
        try:
          # run as classmethod
          if isinstance(hook, classmethod):
            hook.__func__(context, *args, **kwargs)

          # run as staticmethod
          elif isinstance(hook, staticmethod):
            hook.__func__(*args, **kwargs)

          else:

            # must have a singleton if we're running in object context
            if not (
              hasattr(context, '__singleton__') or not context.__singleton__):
              raise RuntimeError('Cannot execute hook method "%s"'
                                 ' without matching singleton context.' % hook)

            # resolve singleton by context name
            obj = Proxy.Component.singleton_map.get(context.__name__)
            if not obj: raise RuntimeError('No matching singleton'
                                           ' for hook method "%s".' % hook)

            # run in singleton context
            hook(point, obj, *args, **kwargs)

        except Exception:
          if __debug__: raise

    return

  def __init__(self, app):

    """  """

    self.application, self.bridge = (
      app,
      Bridge())

  def initialize(self):

    """  """

    self.execute_hooks('initialize', runtime=self)

  def configure(self, config):

    """  """

    self.config = config
    self.initialize()  # let subclasses initialize
    return self

  def serve(self, interface, port, bind_only=False):

    """  """

    server = self.bind(interface, port)

    if bind_only:
      return server

    try:
      server.serve_forever()
    except (KeyboardInterrupt, Exception):
      print("Exiting.")
      sys.exit(0)

  def bind_environ(self, environ):

    """  """

    from ..logic import http
    self.routes = http.HTTPSemantics.route_map.bind_to_environ(environ)

    return (
      http.HTTPSemantics,
      http.HTTPSemantics.new_request(environ),
      http.HTTPSemantics.new_response())

  def handshake(self, key, origin=None):

    """ WIP """

    raise NotImplementedError('Runtime "%s" does not support'
                              ' realtime dispatch semantics. ' % self)

  def send(self, payload, binary=False):

    """ WIP """

    raise NotImplementedError('Runtime "%s" does not support'
                              ' realtime dispatch semantics. ' % self)

  def send(self):

    """ WIP """

    raise NotImplementedError('Runtime "%s" does not support'
                              ' realtime dispatch semantics. ' % self)

  def receive(self):

    """ WIP """

    raise NotImplementedError('Runtime "%s" does not support'
                              ' realtime dispatch semantics. ' % self)

  def dispatch(self, environ, start_response):

    """ WIP """

    from ..base import handler as base_handler

    # setup hook context
    context = {
      'environ': environ,
      'start_response': start_response,
      'runtime': self}

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
        'response': None})

      # dispatch error hook for 404
      self.execute_hooks(('error', 'complete'), **context)

      # noinspection PyCallByClass,PyTypeChecker
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
          'mimetype': content_type})

        # call response hooks
        self.execute_hooks(('response', 'complete'), **context)
        return _response(environ, start_response)

      # unpack response
      status, headers, content_type, content = (
        context['status'],
        context['headers'],
        context['content_type'],
        context['content']
      ) = result.status, result.headers, result.content_type, result.response

      # call response hooks
      self.execute_hooks(('response', 'complete'), **context)

      # send start_response
      start_response(result.status, [(
        k.encode('utf-8').strip(), v.encode('utf-8').strip()
      ) for k, v in result.headers])

      # buffer and return (i guess) @TODO(sgammon): can we do this better?
      return iterator or result.response  # it's a werkzeug Response

    # delegated class-based handlers (for instance, other WSGI apps)
    elif isinstance(handler, type) or callable(handler):

      # make a neat little shim, containing our runtime
      def _foreign_runtime_bridge(status, headers):

        """  """

        # call response hooks
        context['status'], context['headers'], context['response'] = (
          status,
          headers,
          None)

        self.execute_hooks(('response', 'complete'), **context)
        return start_response(status, headers)

      # attach runtime, arguments and actual start_response to shim
      _foreign_runtime_bridge.runtime = self
      _foreign_runtime_bridge.arguments = arguments
      _foreign_runtime_bridge.start_response = start_response
      context['start_response'] = _foreign_runtime_bridge

      # call hooks, initialize foreign handler with replaced start_response
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
          result.headers, result.response)

        self.execute_hooks(('response', 'complete'), **context)

        # it's a Response class - delegate to attached start_response
        return response(environ, start_response)

      # a tuple bound to a URL - static response
      elif isinstance(result, tuple):

        if len(result) == 2:  # it's (status_code, response)
          status, response = (
            context['status'],
            context['response'],
          ) = result

          headers = context['headers'] = [
            ('Content-Type', 'text/html; charset=utf-8')]

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
              headers['Content-Type'] = context['headers']['Content-Type'] = (
                'text/html; charset=utf-8')

          # call response hooks
          self.execute_hooks(('response', 'complete'), **context)
          start_response(status, headers)
          return iter([response])

      elif isinstance(result, basestring):

        status, headers = (
          context['status'],
          context['headers'],
          context['response']
        ) = '200 OK', [('Content-Type', 'text/html; charset=utf-8')]

        # call response hooks
        self.execute_hooks(('response', 'complete'), **context)
        start_response(status, headers)
        return iter([result])

    # could be a bound response
    if not callable(handler):
      if isinstance(handler, basestring):

        context['status'], context['headers'], context['response'] = (
          '200 OK', [('Content-Type', 'text/html; charset=utf-8')], result)

        # call response hooks
        self.execute_hooks(('response', 'complete'), **context)
        return iter([handler])  # it's a static response!

    raise RuntimeError('Unrecognized handler type: "%s".' % type(handler))

  def wrap(self, dispatch):

    """  """

    if not self.__wrapped__:

      # default: return dispatch directly
      _dispatch = dispatch

      # == development wrappers
      dev_config = getattr(self.config, 'app', {}).get('dev', {})

      # profiler support
      if 'profiler' in dev_config:
        profiler_cfg = dev_config['profiler']

        if profiler_cfg.get('enable', False):

          ## grab a profiler
          try:
            import cProfile as profile
          except ImportError:
            import profile

          ## calculate dump file path
          profile_path = profiler_cfg.get('dump_file', os.path.abspath(
            os.path.join(*(os.getcwd(), '.develop', 'app.profile'))))

          ## current profile
          pkwargs = profiler_cfg.get('profile_kwargs', {})
          _current_profile = profile.Profile(**pkwargs)

          ## handle flushing mechanics
          if profiler_cfg.get('on_request', True):

            def maybe_flush_profile():

              """  """

              _current_profile.dump_stats(profile_path)

          else:
            # @TODO(sgammon): cross-request profiling
            raise RuntimeError('Cross-request profiling'
                               ' is currently unsupported.')

          def _dispatch(*args, **kwargs):

            """ Wrapper to enable profiler support. """

            ## dispatch
            response = _current_profile.runcall(dispatch, *args, **kwargs)
            maybe_flush_profile()
            return response

      self.__wrapped__ = _dispatch  # cache locally

    return self.__wrapped__

  def bind(self, interface, port):

    """  """

    raise NotImplementedError

  def callback(self, start_response):

    """  """

    def responder(status, headers):

      """  """

      return start_response(status, headers)

    return responder

  def __call__(self, environ, start_response):

    """  """

    try:
      return self.wrap(self.dispatch)(environ, self.callback(start_response))

    except self.base_exception as exc:
      return exc(environ, start_response)  # it's an acceptable exception

    except Exception:
      raise  # just raise it k?


class Library(object):

  """ Provides a structure that can be used to indicate (and safely handle)
      external dependencies. Used extensively inside Canteen and usable by app
      developers to introduce different functionality depending on the packages
      available. """

  name = None  # string name of the library
  strict = False  # whether to hard-fail on ImportError
  package = None  # reference to the actual library package/module
  exception = None  # captured ImportError or AttributeError exception, if any
  supported = None  # boolean indicating whether this lib is supported or not

  __owner__, __metaclass__ = "Library", Proxy.Component

  def __init__(self, package, strict=False):

    """ Initialize this ``Library`` with a target Python ``package``, and
        optionally ``strict`` mode.

        :param package: ``str`` path to a package that should be imported. When
          ``Library`` is used in a ``with`` block, the library import must be
          successful to proceed in loading/processing the contents of the
          block.

        :param strict: ``bool`` flag to indicate that the developer wishes to
          hard-fail if the given ``package`` is not available. Defaults to
          ``False``, meaning any ``ImportError`` encountered loading ``package``
          will simply be ignored. ``True`` causes the exception to bubble to the
          caller. """

    if isinstance(package, basestring):
      self.name = package
    elif isinstance(package, type(abc)):
      self.name, self.package, self.supported = package.__name__, package, True
    self.strict = strict

  def load(self, *subpackages):

    """ Load a subpackage from an already-constructed/resolved ``Library``
        object. This is usually used from the ``library`` element in a ``with``
        block.

        :param subpackages: Positional arguments are loaded as subpackages/
          submodules from the original ``package`` passed during construciton.
          For instance, ``Library('collections').load('defaultdict')`` is
          essentially equivalent to ``from collections import defaultdict``.

        :raises ImportError: Import issues are directly surfaced from this
          method, as it is designed to be wrapped in a ``with`` block.

        :returns: Loaded ``module`` object. """

    loaded = []
    for package in subpackages:
      loaded.append(importlib.import_module('.'.join((self.name, package))))
    if len(loaded) == 1:
      return loaded[0]  # special case: one package only (return it directly)
    return tuple(loaded)  # otherwise, return a tuple of loaded modules

  def __enter__(self):

    """ Context entrance method, responsible for triggering a load of the top-
        level package and propagating exceptions if ``strict`` mode is active.

        :retunrs: ``tuple`` of the form ``(self, package)``, such that it can
          be unpacked into ``(library, package)`` in a ``with ... as``
          block. """

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

    """  """

    if exception:
      if self.strict: return False

    return True
