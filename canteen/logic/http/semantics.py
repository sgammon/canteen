# -*- coding: utf-8 -*-

"""

  HTTP semantics
  ~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# session API
from .. import session

# core
from canteen.base import logic
from canteen.core import runtime

# canteen util
from canteen.util import config
from canteen.util import decorators


def url(name_or_route, route=None, **kwargs):

  """ Decorator for binding a URL (potentially with a name) to some sort of
      handler, which can really be anything from raw types like a ``str`` or a
      ``tuple`` to a full handler/function/class to a foreign WSGI callable.

      :param name_or_route: Either the route itself (if no name is to be
        provided) or a string name for the route, which can be used to easily
        build URL's to named pages which do not rely on the underlying URL
        structure. Type is always ``basestring``.

      :param route: If a name is provided in ``name_or_route``, this should be
        a ``basestring`` route mapping in Werkzeug style.

      :param kwargs: Keyword arguments to pass to ``add_route``, which is the
        method used to associate the target handler with the given URL. One
        ``kwarg`` is used locally - like many decorators in Canteen, you can
        pass another callable as ``wrap=callable`` and it will be used to chain
        decoration before construction.

      :returns: Decorated target, unchanged, after registration. """

  # extract route and name (optional, but first arg if specified)
  name, route = (None, name_or_route) if not route else (name_or_route, route)

  # must provide at least a route
  if not route: raise ValueError('Cannot bind to a URL with an empty route.')

  # inject the rule factory
  def bind_route(target):

    """ Wrapped closure that applies a URL binding to a target to-be-decorated.

        :param target: Handler to be decorated with this URL binding, by
          associating the two in the currently-active runtime.

        :returns: Decorated ``target``, unchanged, after registration. """

    wrap = kwargs.get('wrap') or (lambda x: x)  # check wrap
    if 'wrap' in kwargs: del kwargs['wrap']

    for entry in ((route,) if not isinstance(route, tuple) else route):
      HTTPSemantics.add_route((entry, name), target, **kwargs)
    return wrap(target)

  return bind_route


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):

  # werkzeug internals
  wsgi, utils, routing, wrappers, exceptions = library.load(
    'wsgi',
    'utils',
    'routing',
    'wrappers',
    'exceptions')


  @decorators.bind('http', namespace=False)
  class HTTPSemantics(logic.Logic):

    """ Packages and provides basic logic to support communication via Hypertext
        Transfer Protocol, versions 1.0-1.1 (support for HTTPv2 soon). """

    # @TODO(sgammon): rename __aliases__ as it clashes with DI
    __aliases__, __map__, __router__ = (
      {}, None, None)  # aliases to routes, routing map cache, route cache


    # == Base Classes == #
    HTTPException = exceptions.HTTPException


    class HTTPRequest(wrappers.BaseRequest,
                      wrappers.AcceptMixin,
                      wrappers.UserAgentMixin,
                      wrappers.AuthorizationMixin,
                      wrappers.CommonRequestDescriptorsMixin):

      """ Base HTTP request wrapper object, backed by Werkzeug's ``BaseRequest``
          and rich functionality mixins.

          Provides the following mixin functionality:
          - ``AcceptMixin`` - HTTP accept header handling
          - ``UserAgentMixin`` - HTTP user-agent header handling
          - ``AuthorizationMixin`` - HTTP authorization header handling
          - ``CommonRequestDescriptorsMixin`` - extra utility attributes """

      # internal slot & accesstor for session
      __session__, session = None, property(lambda self: self.__session__)

      def set_session(self, session_obj, engine=None):

        """ Set the current session by force.

            :param session_obj: Session object to force-assign as the current
              user's session. Either a ``dict`` or a manually-constructed
              :py:class:`canteen.logic.session.Session` object.

            :param engine: Engine to use for committing the session. Defaults
              to ``None``, in which case the currently-active ``engine`` is
              used automatically.

            :returns: ``self``, for chainability. """

        if session_obj and not isinstance(session_obj, session.Session):
          if 'uuid' not in session_obj and 'id' not in session_obj:
            session_obj = None  # no ID or UUID == no session
          else:  # pragma: no cover
            session_obj = session.Session.load((
              session_obj['uuid' if 'uuid' in session_obj else 'id']),
              data=session_obj)

        if self.__session__:  # pragma: no cover
          existing_session, existing_engine = self.__session__
          if not engine: engine = existing_engine

        return setattr(self, '__session__', (session_obj, engine)) or (
          self.__session__)


    class HTTPResponse(wrappers.BaseResponse,
                       wrappers.ETagResponseMixin,
                       wrappers.ResponseStreamMixin,
                       wrappers.WWWAuthenticateMixin,
                       wrappers.CommonResponseDescriptorsMixin):

      """ Base HTTP response wrapper object, backed by Werkzeug's
          ``BaseResponse`` and rich functionality mixins.

          Provides the following mixin functionality:
          - ``ETagResponseMixin`` - provides ETag header handling
          - ``ResponseStreamMixin`` - provides streaming-style response output
          - ``WWWAuthenticateMixin`` - provides HTTP authentication response
          - ``CommonResponseDescriptorsMixin`` - provides common attributes """


    #### ==== Internals ==== ####

    # noinspection PyMethodParameters
    @decorators.classproperty
    def config(cls):  # pragma: no cover

      """ Class-level property accessor for framework/app configuration.

          :returns: Currently-active instance of
            :py:class:`canteen.util.config.Config`. """

      return config.Config().get('http', {'debug': True})

    @property
    def base_headers(self):

      """ Prepare a set of default (*base*) HTTP response headers to be included
          by-default on any HTTP response.

          :returns: ``list`` of ``tuples``, where each is a pair of ``key``-bound
            ``value`` mappings. Because HTTP headers can be repeated, a ``dict``
            is not usable in this instance. """

      return filter(lambda x: x and x[1], [
        ('Cache-Control', 'no-cache; no-store')])

    #### ==== Routing ==== ####
    @classmethod
    def add_route(cls, route, target, **kwargs):

      """ Bind a handler (``target``) to a URL (``route``) and let it respond
          to later requests that match that ``route``.

          :param route: Route to bind the ``target`` to. This is a Werkzeug-
            style URL specification string.

          :param target: Handler that should be dispatched for requests that
            match the given ``route``.

          :param kwargs: Keyword arguments to pass along to the ``target`` upon
            dispatching URLs against it.

          :returns: ``cls``, for chainability. """

      route, name = route

      # compile route and set in routing cache
      cls.router.set(route, (name, target, kwargs))
      if name: cls.__aliases__[name] = route
      return cls

    @classmethod
    def resolve_route(cls, name):

      """ Resolve a handler for a given route ``name``.

          :param name: Name to find a handler for in the currently-active
            ``cls.router``.

          :returns: ``handler`` bound to name ``name`` via a route, or ``None``
            if no such handler could be found. """

      if name in cls.__aliases__:
        name, handler, route_args = cls.router.get(cls.__aliases__[name])
        return handler
      return None

    @classmethod
    def new_request(cls, environ):

      """ Utility to spawn a new HTTP request wrapper object. Constructs an
          instance of :py:class:`cls.HTTPRequest`, which is usually backed by
          Werkzeug's HTTP internals.

          :param environ: WSGI environment (``dict``) to create the request
            wrapper from.

          :returns: Instance of ``cls.HTTPRequest``, filled out with
            ``environ``. """

      return cls.HTTPRequest(environ)

    @classmethod
    def new_response(cls, *args, **kwargs):

      """ Utility to spawn a new HTTP response wrapper obejct. Constructs an
          instance of :py:class:`cls.HTTPResponse`, which is usually backed by
          Werkzeug's HTTP internals.

          :param args: Positional arguments to pass to the HTTP response wrapper
            object's constructor.

          :param kwargs: Keyword arguments to pass to the HTTP response wrapper
            object's constructor.

          :returns: Instance of ``cls.HTTPResponse``, with arguments passed
            along verbatim. """

      return cls.HTTPResponse(*args, **kwargs)

    @decorators.classproperty
    def router(cls):

      """ Class-level property accessor for the current URL router, which keeps
          track of associations between URLs and handlers, which respond to
          requests for a set of URLs.

          Accessing this attribute the first time spawns a new cache for the
          router, and subsequent accesses re-use that cache.

          :returns: Instance of :py:class:`canteen.logic.cache.Cache` to use for
            resolving handlers. """

      from canteen.logic import cache

      if not cls.__router__:
        setattr(cls, '__router__', cache.Caching.spawn('router'))
      return cls.__router__

    @decorators.classproperty
    def routes(cls):

      """ Class-level property generator for the currently-active set of URL
          routes. Makes use of the local ``cls.router`` to iterate over all
          known routes.

          :returns: Yields ``cls.router``-bound routes, one-at-a-time. """

      for _url, (name, target, kwargs) in cls.router.items():
        yield routing.Rule(_url, endpoint=name, **kwargs)

    @decorators.classproperty
    def route_map(cls):

      """ Class-level property accessor for the current routing map, which is
          an instance of :py:class:`werkzeug.routing.Map`, composed of the
          currently-active ruleset for URL routing.

          :returns: Instance of :py:class:`werkzeug.routing.Map`. """

      if not cls.__map__:
        setattr(cls, '__map__', routing.Map([route for route in cls.routes]))
      return cls.__map__

    #### ==== Utilities ==== ####
    @decorators.bind('error', wrap=classmethod)
    def error(cls, code):

      """ Force an HTTP error by integer ``code``, like ``404`` (for error
          state "Not Found") or ``500``. Resolves the appropriate internal
          exception to raise and raises it immeditely.

          :param code: ``int`` HTTP error state code to raise.

          :raises werkzeug.exceptions.HTTPException: Resolves proper exception
            class to raise, which is always a subclass of ``HTTPException``,
            which is provided by Werkzeug. """

      exceptions.abort(code)

    @decorators.bind('redirect', wrap=classmethod)
    def redirect(cls, url=None, name=None, permanent=False, code=None,
                 *args, **kwargs):

      """ Prepare an HTTP redirect to ``url`` or ``name``, where ``name`` is a
          named URL bound earlier via the ``url`` decorator.

          :param url: URL (absolute or relative) to redirect to.

          :param name: Named endpoint (bound previously via ``url`` decorator)
            to generate a URL for and redirect to.

          :param permanent: ``bool`` flag deciding whether to issue a
            'permanent' redirect, which uses the HTTP code 301 instead of the
             standard "302 Found". Defaults to ``False``, in which case an
             HTTP 302 is issued.

          :param code: ``int`` HTTP code to issue for the redirect. Must be
            greater than 299 and less than 399, indicating it is part of the
            standard range of 'redirect' codes in the HTTP spec. Used over the
            ``permanent`` flag if both are issued.

          :returns: Prepared HTTP redirect, ready to be returned from a handler
            dispatch flow. """

      # sanity checks
      if (not url and not name) or (url and name):  # pragma: no cover
        raise TypeError('Must provide either a URL or name to redirect to -'
                        ' not both and at least one or the other.'
                        ' Got "%s" and "%s".' % (url, name))
      return utils.redirect(url if url else cls.url_for(name, *args, **kwargs),
                            code=302 if not permanent else 301)

    # @TODO(sgammon): is this necessary?
    @decorators.bind('response', wrap=classmethod)
    def response(cls, *args, **kwargs):  # pragma: no cover

      """ Property accessor to generate a ``wrappers.Response`` object on the
          fly via DI.

          :param args: Positional arguments to pass to the response wrapper
            constructor.

          :param kwargs: Keyword arguments to pass to the response wrapper
            constructor. """

      return wrappers.Response(*args, **kwargs)

    #### ==== HTTP Methods ==== ####

    # default to a `Method Not Allowed`
    GET = decorators.bind('GET')(lambda self: self.error(405))
    POST = decorators.bind('POST')(lambda self: self.error(405))
    PUT = decorators.bind('PUT')(lambda self: self.error(405))
    HEAD = decorators.bind('HEAD')(lambda self: self.error(405))
    OPTIONS = decorators.bind('OPTIONS')(lambda self: self.error(405))
    TRACE = decorators.bind('TRACE')(lambda self: self.error(405))
