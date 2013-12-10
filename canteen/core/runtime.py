# -*- coding: utf-8 -*-

'''

  canteen runtime core
  ~~~~~~~~~~~~~~~~~~~~

  platform internals and logic to discover/load/inject.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import abc
import importlib

# core API
from .meta import Proxy


class Runtime(object):

  '''  '''

  routes = None  # compiled route map
  config = None  # application config
  handler = None  # resolved handler
  application = None  # WSGI app

  __owner__, __metaclass__ = "Runtime", Proxy.Component

  @classmethod
  def spawn(cls, app):

    '''  '''

    # if we're running as ``Runtime``, resolve a runtime first
    return (cls.resolve() if cls is Runtime else cls)(app)

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

  def __init__(self, app):

    '''  '''

    self.application = app

  def initialize(self):

    '''  '''

    return

  def configure(self, config):

    '''  '''

    self.config = config
    self.initialize()  # let subclasses initialize

    return self

  def serve(self, interface, port):

    '''  '''

    server = self.bind(interface, port)

    try:
      server.serve_forever()
    except KeyboardInterrupt as e:
      print "Exiting."
      exit(0)
    except Exception as e:
      print "Exiting."
      exit(1)

    return

  def bind_environ(self, environ):

    '''  '''

    from ..logic import http
    self.routes = http.HTTPSemantics.route_map.bind_to_environ(environ)
    return self.routes, http.HTTPSemantics

  def dispatch(self, environ, start_response):

    '''  '''

    # resolve URL via bound routes
    routes, http = self.bind_environ(environ)

    # match route
    endpoint, arguments = self.routes.match()

    # resolve endpoint
    handler = http.resolve_route(endpoint)

    if not handler:  # `None` for handler means it didn't match
      http.error(404)

    # initialize handler
    flow = handler(self, environ, start_response)

    if not hasattr(flow, flow.request.method):
      http.error(405)

    # dispatch
    return flow(arguments)(environ, start_response)

  @abc.abstractmethod
  def bind(self, interface, address):

    '''  '''

    raise NotImplementedError

  __call__ = dispatch


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

  def load(self, subpackage):

    '''  '''

    return importlib.import_module('.'.join((self.name, subpackage)))

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

    if exception and exception_cls is NotImplementedError:
      return True
