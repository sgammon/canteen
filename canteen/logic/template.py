# -*- coding: utf-8 -*-

'''

  template logic
  ~~~~~~~~~~~~~~

  exposes base logic for dealing with ``Jinja2`` templates.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os
import json
import operator
import importlib

# core util & base
from ..base import logic
from ..core import runtime
from ..util import decorators


## Globals
_conditionals = []
average = lambda x: reduce(operator.add, x) / len(x)


with runtime.Library('jinja2', strict=True) as (library, jinja2):


  class ChoiceLoader(jinja2.ChoiceLoader):

    '''  '''

    def get_source(self, environment, template):

      '''  '''

      for loader in self.loaders:
        try:
          return loader.get_source(environment, template)
        except (jinja2.TemplateNotFound, RuntimeError, ImportError):
          pass
      raise jinja2.TemplateNotFound(template)

    def load(self, environment, filename, globals=None):

      '''  '''

      for loader in self.loaders:
        try:
          tpl = loader.load(environment, filename, globals)
        except (jinja2.TemplateNotFound, RuntimeError, ImportError):
          pass
        else:
          return tpl
      raise jinja2.TemplateNotFound(filename)


  class ModuleLoader(jinja2.ModuleLoader):

    '''  '''

    cache = None  # cache of modules loaded
    module = None  # main module
    has_source_access = False  # from jinja's internals

    def __init__(self, module='templates'):

      '''  '''

      from canteen.logic.cache import Caching

      if isinstance(module, basestring):
        try:
          module = importlib.import_module(module)
        except ImportError:
          pass
      self.cache, self.module = (
        Caching.spawn('tpl_%s' % module if isinstance(module, basestring) else module.__name__),
        module)

    def load(self, environment, filename, globals=None):

      '''  '''

      globals = globals or {}

      if isinstance(self.module, basestring):
        self.module = importlib.import_module(self.module)

      # Strip '/' and remove extension.
      filename, ext = os.path.splitext(filename.strip('/'))

      t = self.cache.get(filename)
      if not t:
        # Store module to avoid unnecessary repeated imports.
        mod = self.get_module(environment, filename)

        # initialize module
        root, blocks, debug_info = mod.run(environment)

        # manufacture new template object from cached module
        t = object.__new__(environment.template_class)
        t.environment, t.globals, t.name, t.filename, t.blocks  = (
          environment,
          globals,
          mod.name,
          filename,
          blocks
        )

        t.root_render_func, t._module, t._debug_info, t._uptodate = (
          root,
          None,
          debug_info,
          lambda: True
        )

        self.cache.set(filename, t)
      return t

    def get_module(self, environment, template):

      ''' Converts a template path to a package path and attempts import, or else raises Jinja2's TemplateNotFound. '''

      import jinja2

      # Convert the path to a module name.
      prefix, obj = (self.module.__name__ + '.' + template.replace('/', '.').replace('-', '_')).rsplit('.', 1)
      prefix, obj = str(prefix), str(obj)

      try:
        return getattr(__import__(prefix, None, None, [obj]), obj)
      except (ImportError, AttributeError):
        raise jinja2.TemplateNotFound(template)


  class FileLoader(jinja2.FileSystemLoader):

    '''  '''

    has_source_access = True


  class ExtensionLoader(ModuleLoader):

    '''  '''

    pass


  # add loaders to exported items
  _conditionals += [
    'FileLoader',
    'ModuleLoader',
    'ExtensionLoader'
  ]


@decorators.bind('template', namespace=False)
class Templates(logic.Logic):

  '''  '''

  with runtime.Library('jinja2') as (library, jinja2):

    '''  '''

    ## == Attributes == ##
    engine = jinja2  # we're using jinja :)
    default_extensions = property(lambda self: [])
    default_config = property(lambda self: {
      'optimized': True, 'autoescape': True
    })

    # default syntax support method
    def _default_syntax(self, handler, environment_factory, j2config, config):

      '''  '''

      # factory environment
      return environment_factory(**j2config)

    syntax = _default_syntax

    # is there HAML syntax support?
    with runtime.Library('hamlish_jinja') as (haml_library, haml):

      '''  '''

      syntax_extension = (haml.HamlishExtension, haml.HamlishTagExtension)  # we're using haml :)

      def _hamlish_syntax(self, handler, environment_factory, j2config, config):

        '''  '''

        # make environment first
        if 'extensions' not in j2config or not j2config.get('extensions'):

          # make sure standard j2 extensions are added
          j2config['extensions'] = [
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
            'jinja2.ext.do',
            'jinja2.ext.loopcontrols'
          ] + self.default_extensions

        # auto-add hamlish extension
        for ext in self.syntax_extension:
          if ext not in j2config['extensions']:
            j2config['extensions'].append(ext)

        # factory environment
        environment = environment_factory(**j2config)

        if config.debug:
          environment.hamlish_mode, environment.hamlish_debug = 'indented', True

        # apply config overrides
        if 'TemplateAPI' in config.config and 'haml' in config.config['TemplateAPI']:

          for (config_item, target_attr) in (
            ('mode', 'hamlish_mode'),
            ('extensions', 'hamlish_file_extensions'),
            ('div_shortcut', 'hamlish_enable_div_shortcut')):

            if config_item in config.config['TemplateAPI']['haml']:
              setattr(environment, target_attr, config.config['TemplateAPI']['haml'][config_item])

        return environment

      syntax = _hamlish_syntax

    def environment(self, handler, config):

      '''  '''

      # grab template path, if any
      output = config.get('TemplateAPI', {'debug': True})
      path = config.app.get('paths', {}).get('templates')
      jinja2_cfg = output.get('jinja2', self.default_config)

      if not path:
        # default path to cwd, and cwd + templates/, and cwd + templates/source
        cwd = os.getcwd()
        path = (os.path.join(cwd), os.path.join(cwd, 'templates'), os.path.join(cwd, 'templates', 'source'))

      # shim-in our loader system, unless it is overriden in config
      if 'loader' not in jinja2_cfg:

        if (output.get('force_compiled', False)) or (isinstance(path, dict) and 'compiled' in path and (not __debug__)):
          jinja2_cfg['loader'] = ModuleLoader(path['compiled'])

        else:
          jinja2_cfg['loader'] = FileLoader(path['source'] if isinstance(path, dict) else path)

        if 'loader' not in jinja2_cfg:
          raise RuntimeError('No configured template source path.')

      # make our new environment
      j2env = self.syntax(handler, self.engine.Environment, jinja2_cfg, config)

      # allow jinja2 syntax overrides
      if 'syntax' in output:
        for override, directive in filter(lambda x: x[0] in output['syntax'], (
          ('block', ('block_start_string', 'block_end_string')),
          ('comment', ('comment_start_string', 'comment_end_string')),
          ('variable', ('variable_start_string', 'variable_end_string')))):

          # zip and properly set each group
          for group in zip(directive, output['syntax'][override]):
            setattr(j2env, *group)

      # add-in filters
      return j2env.filters.update(self.base_filters) or j2env

  @staticmethod
  def sanitize(content, _iter=True):

    '''  '''

    # content should be a list of content blocks
    content = [content] if not (
      isinstance(content, (tuple, list))) else content

    def sanitize():

      '''  '''

      # iteratively sanitize the response
      for block in content: yield block.strip()

    if _iter: return sanitize()  # return wrapped iterator
    return [block for block in sanitize()]

  @decorators.bind('template.base_headers', wrap=property)
  def base_headers(self):

    '''  '''

    return filter(lambda x: x and x[1], [
      ('Cache-Control', 'no-cache; no-store')
    ])

  @decorators.bind('template.base_context', wrap=property)
  def base_context(self):

    '''  '''

    from canteen.util import config

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
      '__debug__': __debug__ and config.Config().debug,
      'isinstance': isinstance, 'issubclass': issubclass

    }

  @decorators.bind('template.base_filters', wrap=property)
  def base_filters(self):

    '''  '''

    return {

      # Python Builtins (besides the Jinja2 defaults, which are _awesome_)
      'len': len, 'max': max, 'maximum': max, 'min': min, 'minimum': min,
      'avg': average, 'average': average, 'json': json.dumps, 'tojson': json.dumps

    }  # @TODO(sgammon): markdown/RST support?

  @decorators.bind('template.render')
  def render(self, handler, config, template, context, _direct=False):

    '''  '''

    # render template & return content iterato)
    content = self.environment(handler, config).get_template(template).render(**context)

    # if _direct is requested, sanitize and roll-up buffer immediately
    if _direct: return self.sanitize(content, _iter=False)

    # otherwise, buffer/chain iterators to produce a streaming response
    return self.sanitize(content, _iter=True)


__all__ = tuple([
  'Templates'
] + _conditionals)
