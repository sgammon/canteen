# -*- coding: utf-8 -*-

'''

  canteen handler base
  ~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# canteen core
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
  __base_context__ = None  # base template render context

  __owner__, __metaclass__ = "Handler", injection.Compound

  def __init__(self, environ=None, start_response=None, runtime=None, request=None, response=None):

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
  content_type = property(lambda self: self.__content_type__)
  headers = property(lambda self: self.__headers__)

  # shortcuts & utilities
  url_for = lambda self, endpoint, **args: self.routes.build(endpoint, args)

  # WSGI internals
  app = runtime = property(lambda self: self.__runtime__)
  environment = environ = property(lambda self: self.__environ__)
  start_response = callback = property(lambda self: self.__callback__)

  @property
  def agent(self):

    '''  '''

    return self.__agent__

  @property
  def request(self):

    '''  '''

    if not self.__request__:
      self.__request__ = self.http.new_request(self.__environ__)
    return self.__request__

  @property
  def config(self):

    '''  '''

    return config.Config().config

  @property
  def session(self):

    '''  '''

    if self.request.session:
      session, engine = self.request.session
      return session

  @property
  def context(self):

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

  def set_agent(self, fingerprint):

    '''  '''

    return setattr(self, '__agent__', fingerprint) or self

  def render(self, template, headers={}, content_type=None, context={}, _direct=False, **kwargs):

    '''  '''

    if not self.__base_context__:
      self.__base_context__ = {}
      map(self.__base_context__.update, (self.template.base_context, self.context))

    # merge template context
    _merged_context = self.__base_context__
    map(_merged_context.update, (context, kwargs))

    # collapse and merge HTTP headers (base headers first)
    _merged_headers = dict(self.template.base_headers + self.config.get('http', {}).get('headers', {}).items())

    # handler-level headers next
    if self.headers: _merged_headers.update(self.headers)

    # finally, locally-passed headers
    if headers: _merged_headers.update(headers)

    # render template with merged context
    content = self.template.render(*(
      self,
      self.runtime.config,
      template,
      _merged_context
    ), _direct=_direct)

    if _direct:
      return (self.status, _merged_headers, content_type or self.content_type, content)

    else:
      return self.response(content, **{
        'status': self.status,
        'headers': _merged_headers.items(),
        'mimetype': content_type or self.content_type
      })

  def __call__(self, url_args, direct=False):

    '''  '''

    # resolve method to call - try lowercase first
    if not hasattr(self, self.request.method.lower()):
      if not hasattr(self, self.request.method):
        return self.error(405)
      method = getattr(self, self.request.method)
    else:
      method = getattr(self, self.request.method.lower())

    self.__response__ = method(**url_args)
    return self.__response__ if not direct else self


__all__ = ('Handler',)
