# -*- coding: utf-8 -*-

"""

  handler base
  ~~~~~~~~~~~~

  Presents a reasonable base class for a ``Handler`` object, which handles
  responding to an arbitrary "request" for action. For example, ``Handler``
  is useful for responding to HTTP requests *or* noncyclical realtime-style
  requests, and acts as a base class for ``Page`` and ``ServiceHandler``.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import abc
import itertools

# canteen core & util
from ..core import injection
from ..util import decorators


class Handler(object):

  """ Base class structure for a ``Handler`` of some request or desired action.
      Specifies basic machinery for tracking a ``request`` alongside some form
      of ``response``.

      Also keeps track of relevant ``environ`` (potentially from WSGI) and sets
      up a jump off point for DI-provided tools like logging, config, caching,
      template rendering, etc. """

  # @TODO(sgammon): HTTPify, convert to decorator
  config = property(lambda self: {})

  __agent__ = None  # current `agent` details
  __status__ = 200  # it's a glass-half-full kind of day, why not
  __routes__ = None  # route map adapter from werkzeug
  __context__ = None  # holds current runtime context, if any
  __logging__ = None  # internal logging slot
  __runtime__ = None  # reference up to the runtime
  __environ__ = None  # original WSGI environment
  __request__ = None  # lazy-loaded request object
  __headers__ = None  # buffer HTTP header access
  __response__ = None  # lazy-loaded response object
  __callback__ = None  # callback to send data (sync or async)
  __content_type__ = None  # response content type

  # set owner and injection side
  __owner__, __metaclass__ = "Handler", injection.Compound

  def __init__(self, environ=None,
                     start_response=None,
                     runtime=None,
                     request=None,
                     response=None, **context):

    """ Initialize a new ``Handler`` object with proper ``environ`` details and
        inform it of larger world around it.

        ``Handler`` objects (much like ``Runtime`` objects) are designed to be
        usable independently as a WSGI-style callable. Note that the first two
        position parameters of this ``__init__`` are the venerable ``environ``
        and ``start_response`` - dispatching this way is totally possible, but
        providing ``runtime``, ``request`` and ``response`` allow tighter
        integration with the underlying runtime.

        Current execution details (internal to Canteen) are passed as ``kwargs``
          and compounded as new context items are added.

        :param environ: WSGI environment, provided by active runtime. ``dict``
          in standard WSGI format.

        :param start_response: Callable to begin the response cycle. Usually a
          vanilla ``function``.

        :param runtime: Currently-active Canteen runtime. Always an instance of
          :py:class:`canteen.core.runtime.Runtime` or a subclass thereof.

        :param request: Object to use for ``self.request``. Usually an instance
          of :py:class:`werkzeug.wrappers.Request`.

        :param response: Object to use for ``self.response``. Usually an
          instance of :py:class:`werkzeug.wrappers.Response`. """

    # startup/assign internals
    self.__runtime__, self.__environ__, self.__callback__ = (
      runtime,  # reference to the active runtime
      environ,  # reference to WSGI environment
      start_response)  # reference to WSGI callback

    # setup HTTP/dispatch stuff
    self.__status__, self.__headers__, self.__content_type__ = (
      200,  # default response stauts
      {},  # default repsonse headers
      'text/html; charset=utf-8')  # default content type

    # request, response & context
    self.__request__, self.__response__, self.__context__ = (
        request, response, context)

  # expose internals, but write-protect
  routes = property(lambda self: self.__runtime__.routes)
  status = property(lambda self: self.__status__)
  headers = property(lambda self: self.__headers__)
  content_type = property(lambda self: self.__content_type__)

  # shortcuts & utilities
  url_for = link = lambda self, end, **args: self.routes.build(end, args)

  # WSGI internals
  app = runtime = property(lambda self: self.__runtime__)
  environment = environ = property(lambda self: self.__environ__)
  start_response = callback = property(lambda self: self.__callback__)

  # Context
  session = property(lambda self: (  # session is tuple of (session, engine)
    self.request.session[0] if self.request.session else None))

  # Agent
  agent = property(lambda self: (
    self.__agent__ if self.__agent__ else (
      setattr(self, '__agent__', self.http.agent.scan(self.request)) or (
        self.__agent__))))

  # Request & Response
  request = property(lambda self: (
    self.__request__ if self.__request__ else (
      setattr(self, '__request__', self.http.new_request(self.__environ__)) or (
        self.__request__))))

  response = property(lambda self: (
    self.__response__ if self.__response__ else (
      setattr(self, '__response__', self.http.new_response()) or (
        self.__response__))))

  @property
  def template_context(self):

    """ Generate template context to be used in rendering source templates. The
        ``template_context`` accessor is expected to return a ``dict`` of
        ``name=>value`` pairs to present to the template API.

        :returns: ``dict`` of template context. """

    # for javascript context
    from canteen.rpc import ServiceHandler

    return {

      # Default Context
      'handler': self,
      'config': getattr(self, 'config', {}),
      'runtime': self.runtime,

      # HTTP Context
      'http': {
        'agent': getattr(self, 'agent', None),
        'request': self.request,
        'response': self.response
      },

      # WSGI internals
      'wsgi': {
        'environ': self.environ,
        'callback': self.callback,
        'start_response': self.start_response
      },

      # Cache API
      'cache': {
        'get': self.cache.get,
        'get_multi': self.cache.get_multi,
        'set': self.cache.set,
        'set_multi': self.cache.set_multi,
        'delete': self.cache.delete,
        'delete_multi': self.cache.delete_multi,
        'clear': self.cache.clear,
        'flush': self.cache.flush
      },

      # Assets API
      'asset': {
        'image': self.assets.image_url,
        'style': self.assets.style_url,
        'script': self.assets.script_url
      },

      # Service API
      'services': {
        'list': ServiceHandler.services,
        'describe': ServiceHandler.describe
      },

      # Output API
      'output': {
        'render': self.template.render,
        'environment': self.template.environment
      },

      # Routing
      'link': self.url_for,

      'route': {
        'build': self.url_for,
        'resolve': self.http.resolve_route
      }

    }

  def respond(self, content=None):

    """ Respond to this ``Handler``'s request with raw ``str`` or ``unicode``
        content. UTF-8 encoding happens if necessary.

        :param content: Content to respond to. Must be ``str``, ``unicode``, or
          a similar string buffer object.

        :returns: Generated (filled-in) ``self.response`` object. """

    # today is a good day
    if not self.status: self.__status__ = 200
    if content: self.response.response = content

    # set status code and return
    return setattr(self.response,
                  ('status_code' if isinstance(self.status, int) else 'status'),
                    self.status) or (
                  (i.encode('utf-8').strip() for i in self.response.response),
                    self.response)

  def render(self, template,
                   headers=None,
                   content_type='text/html; charset=utf-8',
                   context=None,
                   _direct=False, **kwargs):

    """ Render a source ``template`` for the purpose of responding to this
        ``Handler``'s request, given ``context`` and proper ``headers`` for
        return.

        ``kwargs`` are taken as extra template context and overlayed onto
        ``context`` before render.

        :param template: Path to template file to serve. ``str`` or ``unicode``
          file path.

        :param headers: Extra headers to send with response. ``dict`` or iter of
          ``(name, value)`` tuples.

        :param content_type: Value to send for ``Content-Type`` header. ``str``,
          defaults to ``text/html; charset=utf-8``.

        :param context: Extra template context to include during render.
          ``dict`` of items, with keys as names that values are bound to in the
          resulting template context.

        :param _direct: Flag indicating that ``self`` should be returned, rather
          than ``self.response``. Bool, defaults to ``False`` as this
          technically breaks WSGI.

        :returns: Rendered template content, added to ``self.response``. """

    from canteen.util import config

    # set mime type
    if content_type: self.response.mimetype = content_type

    # collapse and merge HTTP headers (base headers first)
    self.response.headers.extend(itertools.chain(
      iter(self.http.base_headers),
      self.config.get('http', {}).get('headers', {}).iteritems(),
      self.headers.iteritems(),
      (headers or {}).iteritems()))

    # merge template context
    _merged_context = dict(itertools.chain(*(i.iteritems() for i in (
      self.template.base_context,
      self.template_context,
      context or {},
      kwargs))))

    # render template and set as response data
    self.response.response, self.response.direct_passthrough = (
      self.template.render(
        self,
        getattr(self.runtime, 'config', None) or config.Config(),
        template,
        _merged_context)), True

    return self.respond()

  def dispatch(self, **url_args):

    ''' WIP '''

      # resolve method to call - try lowercase first
    method = getattr(self, self.request.method)
    _response = method(**url_args)
    if _response is not None:
      self.__response__ = _response
    return self.__response__

  def __call__(self, url_args, direct=False):

    """ Kick off the local response dispatch process, and run any necessary
        pre/post hooks (named ``prepare`` and ``destroy``, respectively).

        :param url_args: Arguments parsed from URL according to matched route.
          ``dict`` of ``{param: value}`` pairs.

        :param direct: Flag to indicate 'direct' mode, whereby a handler is
          returned instead of a response. Bool, defaults to ``False``, as this
          technically breaks WSGI.

        :returns: ``self.response`` if ``direct`` mode is not active, otherwise
          ``self`` for chainability. """

    # run prepare hook, if specified
    if hasattr(self, 'prepare'): self.prepare(url_args, direct=direct)

    # dispatch local handler, expected to fill `self.__response__`
    self.dispatch(**url_args)

    # run destroy hook, if specified
    if hasattr(self, 'destroy'): self.destroy(self.__response__)

    return self.__response__ if not direct else self


class RealtimeHandler(Handler):

  ''' WIP  '''

  def dispatch(self, **url_args):

    ''' WIP '''

    # fallback to standard dispatch
    if self.realtime.hint not in self.environ:
      return super(RealtimeHandler, self).dispatch(**url_args)

    try:
      # websocket upgrade and session
      self.socket = self.realtime.on_connect(self.runtime, self.request)

      # bind local on_message and begin realtime flow
      self.realtime.on_message(*(
        self.runtime,
        self.environ,
        self.on_message,
        self.runtime.send))

    except NotImplementedError:
      return self.error(400)  # raised when a non-websocket handler is hit

  def on_connect(self, socket):

    ''' WIP '''

    return NotImplemented

  def on_message(self, message):

    ''' WIP '''

    raise NotImplementedError()


__all__ = ('Handler',)
