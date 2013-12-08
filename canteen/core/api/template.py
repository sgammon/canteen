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

# stdlib
import os, sys

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

      # grab template path, if any
      output = handler.runtime.config.get('TemplateAPI', {'debug': True})
      path = handler.runtime.config.app.get('paths', {}).get('templates', 'templates/')
      jinja2_cfg = output.get('jinja2', {
        'autoescape': True,
        'extensions': (
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
        )
      })

      if 'loader' not in jinja2_cfg:
        if ((not __debug__) or output.get('force_compiled', False)) and isinstance(path, dict) and 'compiled' in path:
          jinja2_cfg['loader'] = ModuleLoader('templates')  # @TODO(sgammon): fix this hard-coded value
        else:
          if isinstance(path, dict) and 'source' not in path:
            raise RuntimeError('No configured template source path.')
          jinja2_cfg['loader'] = FileLoader(path['source'] if isinstance(path, dict) else path)
      return self.engine.Environment(**jinja2_cfg)

  @decorators.bind('template.base_headers', wrap=property)
  def base_headers(self):

    '''  '''

    import canteen

    return filter(lambda x: x and x[1], [

      ('Cache-Control', 'no-cache; no-store'),
      ('X-UA-Compatible', 'IE=edge,chrome=1'),
      ('Access-Control-Allow-Origin', '*'),
      ('X-Debug', '1' if canteen.debug else '0'),
      ('Vary', 'Accept,Cookie'),
      ('Server', 'canteen/%s Python/%s' % (
        '.'.join(map(unicode, canteen.__version__)),
        '.'.join(map(unicode, (
          sys.version_info.major,
          sys.version_info.minor,
          sys.version_info.micro
        )))
      )) if __debug__ else ('Server', 'canteen/Python')

    ])

  @decorators.bind('template.base_context')
  def base_context(self, handler):

    '''  '''

    return {

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

  @decorators.bind('template.render')
  def render(self, handler, template, context):

    '''  '''

    # calculate response headers and send

    # render template
    content = self.environment(handler, **handler.runtime.config.get('TemplateAPI')).get_template(template).render(**context)

    # return content iterator
    return iter([content])
