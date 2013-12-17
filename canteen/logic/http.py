# -*- coding: utf-8 -*-

'''

  canteen HTTP logic
  ~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import re

# core
from ..base import logic
from ..core import runtime
from ..util import decorators

# cache API
from ..core.api import cache


def url(name_or_route, route=None, **kwargs):

  '''  '''

  # extract route and name (optional, but first arg if specified)
  name, route = (None, name_or_route) if not route else (name_or_route, route)

  # must provide at least a route
  if not route: raise ValueError('Cannot bind to a URL with an empty route.')

  # inject the rule factory
  def inject(target):

    '''  '''

    for entry in ((route,) if not isinstance(route, tuple) else route):
      HTTPSemantics.add_route((entry, name), target, **kwargs)
    return target

  return inject


with runtime.Library('werkzeug') as (library, werkzeug):

  # werkzeug internals
  wsgi, utils, routing, wrappers, exceptions = library.load(
    'wsgi',
    'utils',
    'routing',
    'wrappers',
    'exceptions'
  )


  @decorators.bind('http', namespace=False)
  class HTTPSemantics(logic.Logic):

    '''  '''

    __aliases__ = {}  # aliases to routes
    __router__ = None  # route cache

    # == Base Classes == #
    HTTPException = exceptions.HTTPException

    #### ==== Routing ==== ####
    @classmethod
    def add_route(cls, (route, name), target, **kwargs):

      '''  '''

      # compile route and set in routing cache
      cls.router.set(route, (name, target, kwargs))
      if name: cls.__aliases__[name] = route

    @classmethod
    def resolve_route(cls, name):

      '''  '''

      if name in cls.__aliases__:
        name, handler, route_args = cls.router.get(cls.__aliases__[name])
        return handler
      return None

    @classmethod
    def new_request(cls, environ):

      '''  '''

      return wrappers.Request(environ)

    @classmethod
    def new_response(cls, *args, **kwargs):

      '''  '''

      return wrappers.Response(*args, **kwargs)

    @decorators.classproperty
    def router(cls):

      '''  '''

      if not cls.__router__:
        cls.__router__ = cache.CacheAPI.spawn('router')
      return cls.__router__

    @decorators.classproperty
    def routes(cls):

      '''  '''

      for url, (name, target, kwargs) in cls.router.items():
        yield routing.Rule(url, endpoint=name, **kwargs)

    @decorators.classproperty
    def route_map(cls):

      '''  '''

      return routing.Map([route for route in cls.routes])

    #### ==== Utilities ==== ####
    @decorators.bind('error', wrap=classmethod)
    def error(cls, code):

      '''  '''

      exceptions.abort(code)

    @decorators.bind('redirect', wrap=classmethod)
    def redirect(cls, url_or_page, permanent=False):

      '''  '''

      pass

    @decorators.bind('response', wrap=classmethod)
    def response(cls, *args, **kwargs):

      '''  '''

      return wrappers.Response(*args, **kwargs)

    #### ==== HTTP Methods ==== ####
    @decorators.bind('GET')
    def GET(self):

      '''  '''

      # default to a `Method Not Allowed`
      self.error(405)

    @decorators.bind('POST')
    def POST(self):

      '''  '''

      # default to a `Method Not Allowed`
      self.error(405)

    @decorators.bind('PUT')
    def PUT(self):

      '''  '''

      # default to a `Method Not Allowed`
      self.error(405)

    @decorators.bind('HEAD')
    def HEAD(self):

      '''  '''

      # default to a `Method Not Allowed`
      self.error(405)

    @decorators.bind('OPTIONS')
    def OPTIONS(self):

      '''  '''

      # default to a `Method Not Allowed`
      self.error(405)

    @decorators.bind('TRACE')
    def TRACE(self):

      '''  '''

      # default to a `Method Not Allowed`
      self.error(405)
