# -*- coding: utf-8 -*-

'''

  canteen: HTTP semantics
  ~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core
from canteen.base import logic
from canteen.core import runtime

# canteen util
from canteen.util import config
from canteen.util import decorators

# cache & session APIs
from canteen.core.api import cache
from canteen.core.api import session


def url(name_or_route, route=None, **kwargs):

  '''  '''

  # extract route and name (optional, but first arg if specified)
  name, route = (None, name_or_route) if not route else (name_or_route, route)

  # must provide at least a route
  if not route: raise ValueError('Cannot bind to a URL with an empty route.')

  # inject the rule factory
  def inject(target):

    '''  '''

    wrap = None  # check wrap
    if 'wrap' in kwargs:
      wrap = kwargs['wrap']
      del kwargs['wrap']

    for entry in ((route,) if not isinstance(route, tuple) else route):
      HTTPSemantics.add_route((entry, name), target, **kwargs)

    if wrap:
      return wrap(target)
    return target

  return inject


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):

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

    __aliases__ = {}  # aliases to routes  # @TODO(sgammon): rename this, it clashes with DI
    __map__ = None  # routing map cache
    __router__ = None  # route cache

    # == Base Classes == #
    HTTPException = exceptions.HTTPException


    class HTTPRequest(wrappers.BaseRequest,
                      wrappers.AcceptMixin,
                      wrappers.UserAgentMixin,
                      wrappers.AuthorizationMixin,
                      wrappers.CommonRequestDescriptorsMixin):

      '''  '''

      __session__ = None  # internal slot for session reference

      @property
      def session(self):

        '''  '''

        return self.__session__

      def set_session(self, session_obj, engine=None):

        '''  '''

        if session_obj and not isinstance(session_obj, session.Session):
          if 'uuid' not in session_obj and 'id' not in session_obj:
            session_obj = None  # no ID or UUID == no session
          else:
            session_obj = session.Session.load(session_obj['uuid' if 'uuid' in session_obj else 'id'], data=session_obj)

        if self.__session__:

          existing_session, existing_engine = self.__session__
          if not engine:
            engine = existing_engine

        self.__session__ = (session_obj, engine)
        return self


    class HTTPResponse(wrappers.BaseResponse,
                       wrappers.ETagResponseMixin,
                       wrappers.ResponseStreamMixin,
                       wrappers.WWWAuthenticateMixin,
                       wrappers.CommonResponseDescriptorsMixin):

      '''  '''

      pass

    #### ==== Internals ==== ####
    @decorators.classproperty
    def config(cls):

      '''  '''

      return config.Config().get('http', {'debug': True})

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

      return cls.HTTPRequest(environ)

    @classmethod
    def new_response(cls, *args, **kwargs):

      '''  '''

      return cls.HTTPResponse(*args, **kwargs)

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

      if not cls.__map__:
        cls.__map__ = routing.Map([route for route in cls.routes])
      return cls.__map__

    #### ==== Utilities ==== ####
    @decorators.bind('error', wrap=classmethod)
    def error(cls, code):

      '''  '''

      exceptions.abort(code)

    @decorators.bind('redirect', wrap=classmethod)
    def redirect(cls, url=None, name=None, permanent=False, *args, **kwargs):

      '''  '''

      # sanity checks
      if (not url and not name) or (url and name):
        raise TypeError('Must provide either a URL or name to redirect to - not both and at least one or the other. Got "%s" and "%s".' % (url, name))
      return utils.redirect(url if url else self.url_for(name, *args, **kwargs), code=302 if not permanent else 301)

    @decorators.bind('response', wrap=classmethod)
    def response(cls, *args, **kwargs):

      '''  '''

      return wrappers.Response(*args, **kwargs)

    #### ==== HTTP Methods ==== ####
    @decorators.bind('GET')
    def GET(self):

      '''  '''

      self.error(405)  # default to a `Method Not Allowed`

    @decorators.bind('POST')
    def POST(self):

      '''  '''

      self.error(405)  # default to a `Method Not Allowed`

    @decorators.bind('PUT')
    def PUT(self):

      '''  '''

      self.error(405)  # default to a `Method Not Allowed`

    @decorators.bind('HEAD')
    def HEAD(self):

      '''  '''

      self.error(405)  # default to a `Method Not Allowed`

    @decorators.bind('OPTIONS')
    def OPTIONS(self):

      '''  '''

      self.error(405)  # default to a `Method Not Allowed`

    @decorators.bind('TRACE')
    def TRACE(self):

      '''  '''

      self.error(405)  # default to a `Method Not Allowed`


    __all__ = (
      'url',
      'HTTPSemantics'
    )
