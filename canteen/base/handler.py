# -*- coding: utf-8 -*-

'''

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

'''

# stdlib
import itertools

# canteen core & util
from ..core import injection
from ..util import decorators


@decorators.configured
class Handler(object):

  ''' Base class structure for a ``Handler`` of some request or desired action.
      Specifies basic machinery for tracking a ``request`` alongside some form
      of ``response``.

      Also keeps track of relevant ``environ`` (potentially from WSGI) and sets
      up a jump off point for DI-provided tools like logging, config, caching,
      template rendering, etc. '''

  # @TODO(sgammon): HTTPify
  config = property(lambda self: {})

  __agent__ = None  # current `agent` details
  __status__ = 200  # keen is an optimistic bunch ;)
  __routes__ = None  # route map adapter from werkzeug
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
                     response=None):

    ''' Initialize a new ``Handler`` object with proper ``environ`` details and
        inform it of larger world around it.

        ``Handler`` objects (much like ``Runtime`` objects) are designed to be
        usable independently as a WSGI-style callable. Note that the first two
        position parameters of this ``__init__`` are the venerable ``environ``
        and ``start_response`` - dispatching this way is totally possible, but
        providing ``runtime``, ``request`` and ``response`` allow tighter
        integration with the underlying runtime.

        Args:
          :param environ:
          :type environ:

          :param start_response:
          :type start_response:

          :param runtime:
          :type runtime:

          :param request:
          :type request:

          :param response:
          :type response:

        '''

    # startup/assign internals
    self.__runtime__, self.__environ__, self.__callback__ = (
      runtime,  # reference to the active runtime
      environ,  # reference to WSGI environment
      start_response  # reference to WSGI callback
    )

    # setup HTTP/dispatch stuff
    self.__status__, self.__headers__, self.__content_type__ = (
      200,  # default response stauts
      {},  # default repsonse headers
      'text/html; charset=utf-8'  # default content type
    )

    # request & response
    self.__request__, self.__response__ = request, response

  # expose internals, but write-protect
  runtime = property(lambda self: self.__runtime__)
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

    ''' Generate template context to be used in rendering source templates. The
        ``template_context`` accessor is expected to return a ``dict`` of
        ``name=>value`` pairs to present to the template API.

        :returns: ``dict`` of template context. '''

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

  def render(self, template,
                   headers={},
                   content_type='text/html',
                   context={},
                   _direct=False, **kwargs):

    ''' Render a source ``template`` for the purpose of responding to this
        ``Handler``'s request, given ``context`` and proper ``headers`` for
        return.

        Args:
          :param template:
          :type template:

          :param headers:
          :type headers:

          :param content_type:
          :type content_type:

          :param context:
          :type context:

          :param _direct:
          :type _direct:

        Kwargs:


        :returns: '''

    from canteen.util import config

    # set mimetype
    if content_type: self.response.mimetype = content_type

    # collapse and merge HTTP headers (base headers first)
    self.response.headers.extend(itertools.chain(
      iter(self.template.base_headers),
      self.config.get('http', {}).get('headers', {}).iteritems(),
      self.headers.iteritems(),
      headers.iteritems()
    ))

    # merge template context
    _merged_context = dict(itertools.chain(*(i.iteritems() for i in (
      self.template.base_context,
      self.template_context,
      context,
      kwargs
    ))))

    # render template and set as response data
    self.response.response, self.response.direct_passthrough = (
      self.template.render(
        self,
        getattr(self.runtime, 'config', config.Config()),
        template,
        _merged_context
      )), True

    return self.respond()

  def respond(self, content=None):

    ''' Respond to this ``Handler``'s request with raw ``str`` or ``unicode``
        content. UTF-8 encoding happens if necessary.

        Args:
          :param content:
          :type content:

        :returns: '''

    # today is a good day
    if not self.status: self.status = 200
    if content: self.response.response = content

    # set status code and return
    return setattr(self.response,
                  ('status_code' if isinstance(self.status, int) else 'status'),
                    self.status) or (
                  (i.encode('utf-8').strip() for i in self.response.response),
                  self.response)

  def __call__(self, url_args, direct=False):

    ''' Kick off the local response dispatch process, and run any necessary
        pre/post hooks (named ``prepare`` and ``destroy``, respectively).

        Args:
          :param url_args:
          :type url_args:

          :param direct:
          :type direct:

        :returns: '''

    # run prepare hook, if specified
    if hasattr(self, 'prepare'):
      self.prepare(url_args, direct=direct)

    # resolve method to call - try lowercase first
    if not hasattr(self, self.request.method.lower().strip()):
      if not hasattr(self, self.request.method):
        return self.error(405)
      method = getattr(self, self.request.method)
    else:
      method = getattr(self, self.request.method.lower())

    self.__response__ = method(**url_args)

    # run destroy hook, if specified
    if hasattr(self, 'destroy'):
      self.destroy(self.__response__)

    return self.__response__ if not direct else self


__all__ = ('Handler',)
