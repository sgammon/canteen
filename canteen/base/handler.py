# -*- coding: utf-8 -*-

'''

  canteen: handler base
  ~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import itertools

# canteen core
from ..core import hooks
from ..core import injection

# canteen util
from ..util import debug
from ..util import config


## Globals
_logger = debug.Logger('Handler')
_logger.addHandler(debug.logging.StreamHandler())


class Handler(object):

  '''  '''

  logging  = _logger  # local logging shim
  __agent__ = None  # current `agent` details
  __status__ = 200  # keen is an optimistic bunch ;)
  __config__ = None  # configuration for this handler
  __routes__ = None  # route map adapter from werkzeug
  __logging__ = None  # internal logging slot
  __runtime__ = None  # reference up to the runtime
  __environ__ = None  # original WSGI environment
  __request__ = None  # lazy-loaded request object
  __headers__ = None  # buffer HTTP header access
  __response__ = None  # lazy-loaded response object
  __callback__ = None  # callback to send data (sync or async)
  __content_type__ = None  # response content type

  __owner__, __metaclass__ = "Handler", injection.Compound

  def __init__(self, environ=None, start_response=None, runtime=None, request=None, response=None, **context):

    '''  '''

    # startup/assign internals
    self.__runtime__, self.__environ__, self.__callback__ = (
      runtime,
      environ,
      start_response
    )

    # setup HTTP/dispatch stuff
    self.__status__, self.__headers__, self.__content_type__ = (
      200,
      {},
      'text/html'
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
  url_for = link = lambda self, endpoint, **args: self.routes.build(endpoint, args)

  # WSGI internals
  app = runtime = property(lambda self: self.__runtime__)
  environment = environ = property(lambda self: self.__environ__)
  start_response = callback = property(lambda self: self.__callback__)

  # Context
  config = property(lambda self: config.Config().config)
  session = property(lambda self: self.request.session[0] if self.request.session else None)  # session is tuple of (session, engine)

  # Agent
  agent = property(lambda self: self.__agent__ if self.__agent__ else (setattr(self, '__agent__', self.http.agent.scan(self.request)) or self.__agent__))

  # Request & Response
  request = property(lambda self: self.__request__ if self.__request__ else (setattr(self, '__request__', self.http.new_request(self.__environ__)) or self.__request__))
  response = property(lambda self: self.__response__ if self.__response__ else (setattr(self, '__response__', self.http.new_response()) or self.__response__))

  @property
  def template_context(self):

    '''  '''

    # for javascript context
    from canteen.rpc import ServiceHandler

    return {

      # Default Context
      'handler': self,
      'config': self.runtime.config,
      'runtime': self.runtime,

      # HTTP Context
      'http': {
        'request': self.request,
        'response': self.response
      },

      # WSGI internals
      'wsgi': {
        'environ': self.environ,
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

  def render(self, template, headers={}, content_type='text/html', context={}, _direct=False, **kwargs):

    '''  '''

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
    self.response.response, self.response.direct_passthrough = self.template.render(
      self,
      self.runtime.config,
      template,
      _merged_context
    ), True

    # set status code and return
    return setattr(self.response,
      ('status_code' if isinstance(self.status, int) else 'status'),
      self.status
    ) or ((i.encode('utf-8').strip() for i in self.response.response), self.response)

  def __call__(self, url_args, direct=False):

    '''  '''

    # resolve method to call - try lowercase first
    if not hasattr(self, self.request.method.lower().strip()):
      if not hasattr(self, self.request.method):
        return self.error(405)
      method = getattr(self, self.request.method)
    else:
      method = getattr(self, self.request.method.lower())

    self.__response__ = method(**url_args)
    return self.__response__ if not direct else self


__all__ = ('Handler',)
