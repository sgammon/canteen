# -*- coding: utf-8 -*-

'''

  canteen: core template API
  ~~~~~~~~~~~~~~~~~~~~~~~~~~

  exposes a core API for interfacing with template engines
  like :py:mod:`Jinja2`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# core API & util
from . import CoreAPI
from .. import runtime
from .cache import CacheAPI
from canteen.util import decorators


with runtime.Library('jinja2') as (library, jinja2):


  class TemplateLoader(jinja2.FileSystemLoader):

    '''  '''

    pass


  class ModuleLoader(TemplateLoader):

    '''  '''

    has_source_access = False

    def __init__(self, template):

      '''  '''

      self.modules, self.template = CacheAPI.spawn('tpl_%s' % template), template

    def prepare_template(self, environment, filename, tpl_vars, globals):

      '''  '''

      pass

    def load(self, environment, filename, globals=None, prepare=True):

      '''  '''

      if globals is None:
        globals = {}

    def get_module(self, environment, template):

      '''  '''

      pass


  class FileLoader(TemplateLoader):

    '''  '''

    has_source_access = True

    def get_source(self, environment, name):

      '''  '''

      # retrieve source / uptodate-ness
      return super(TemplateLoader, self).get_source(environment, name)


@decorators.bind('template', namespace=False)
class TemplateAPI(CoreAPI):

  '''  '''

  with runtime.Library('jinja2') as (library, jinja2):

    '''  '''

    @property
    def engine(self):

      '''  '''

      return jinja2

    def environment(self, handler, **kwargs):

      '''  '''

      import pdb; pdb.set_trace()

      # grab template path, if any
      output = handler.runtime.config.get('TemplateAPI', {'debug': True})
      path = handler.runtime.config.app.get('paths', {}).get('templates', 'templates/')

      return self.engine.Environment(**kwargs)

  @decorators.bind('template.base_headers')
  def base_headers(self):

    '''  '''

    import canteen

    return filter(lambda x: x and x[1], [

      ('Cache-Control', 'no-cache; no-store'),
      ('X-Powered-By', 'canteen/%s' % '.'.join(canteen.__version__)),
      ('X-UA-Compatible', 'IE=edge,chrome=1'),
      ('Access-Control-Allow-Origin', '*'),
      ('X-Debug', '1' if canteen.debug else '0'),
      ('Vary', 'Accept,Cookie')

    ])

  @decorators.bind('template.base_context')
  def base_context(self, handler):

    '''  '''

    baseContext = {

      # Python Builtins
      'all': all, 'any': any,
      'int': int, 'str': str,
      'len': len, 'map': map,
      'max': max, 'min': min,
      'enumerate': enumerate,
      'zip': zip, 'bool': bool,
      'list': list, 'dict': dict,
      'tuple': tuple, 'range': range,
      'round': round, 'slice': slice,
      'xrange': xrange, 'filter': filter,
      'reduce': reduce, 'sorted': sorted,
      'unicode': unicode, 'reversed': reversed,
      'isinstance': isinstance, 'issubclass': issubclass,

      # Routing
      'routing': {
        'build': handler.routes.build,
        'resolve': handler.http.resolve_route
      }

    }

    if hasattr(handler, 'context'):
      baseContext.update(handler.context)
    return baseContext

  @decorators.bind('template.render', wrap=classmethod)
  def render(self, handler, template, context):

    '''  '''

    # calculate response headers and send
    import pdb; pdb.set_trace()

    # render template
    content = self.environment(handler, **handler.config.get('TemplateAPI')).get_template(template).render(**context)

    # return content iterator
    return iter([content])
