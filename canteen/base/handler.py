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
from ..util import decorators


## Globals
_logger = debug.Logger('Handler')
_logger.addHandler(debug.logging.StreamHandler())


class Handler(object):

  '''  '''

  logging  = _logger
  __config__ = None  # configuration for this handler
  __logging__ = None  # internal logging slot
  __runtime__ = None  # reference up to the runtime
  __environ__ = None  # original WSGI environment
  __request__ = None  # lazy-loaded request object
  __response__ = None  # lazy-loaded response object
  __callback__ = None  # callback to send data (sync or async)

  __owner__, __metaclass__ = "Handler", injection.Compound

  def __init__(self, runtime, environ, start_response):

    '''  '''

    self.__runtime__, self.__environ__, self.__callback__ = (
      runtime,
      environ,
      start_response
    )

  @property
  def runtime(self):

    '''  '''

    return self.__runtime__  # protect `__runtime__` from writes

  @property
  def request(self):

    '''  '''

    if not self.__request__:
      self.__request__ = self.http.new_request(self.__environ__)
    return self.__request__

  @property
  def config(self):

    '''  '''

    if not self.__config__:
      # scan for config, walking up the class chain to fallback
      done, base, config = False, self.__class__, []

      while not done:

        for cls in base.__bases__:
          # calculate config path, optionally deferring to `__path__`
          path = getattr(base, '__path__') if hasattr(base, '__path__') else (
            '.'.join((cls.__module__, cls.__name__))
          )

          # if it's found, merge + return
          if path in self.runtime.config:
            config.append(self.runtime.config[path])

        # otherwise jump up in bases and continue searching
        if base.__class__ not in (object, type):
          base = base.__class__
        else:
          done = True

      else:
        self.__config__ = {'debug': True}

      _merged = {}
      for block in reversed(config):
        _merged.update(block)

      if not _merged:  # empty still?
        self.__config__ = {'debug': True}
      else:
        self.__config__ = _merged
    return self.__config__

  @property
  def context(self):

    '''  '''

    return {

      # Default Context
      'self': self,
      'config': self.config,
      'runtime': self.runtime,

      # HTTP Context
      'http': {
        'request': self.request,
        'response': self.response
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

      },

      # Output API
      'output': {

      },

    }

  def render(self, template, context={}, **kwargs):

    '''  '''

    _merged_context = {}
    for context_block in (self.context, context, kwargs):
      _merged_context.update(context_block)

    # render template with merged context
    return self.template.render(self, template, _merged_context)


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
