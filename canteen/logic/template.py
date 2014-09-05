# -*- coding: utf-8 -*-

"""

  template logic
  ~~~~~~~~~~~~~~

  exposes base logic for dealing with ``Jinja2`` templates.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

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


  class ModuleLoader(jinja2.ModuleLoader):

    """ ``Jinja2`` :py:class:`TemplateLoader`, responsible for resolving Python-
        optimized template routines. When ``Jinja2`` templates are compiled to
        raw Python, this is the loader that is responsible for
        importing/executing/preparing responses from those templates. """

    cache = None  # cache of modules loaded
    module = None  # main module
    has_source_access = False  # from jinja's internals

    def __init__(self, module='templates'):

      """ Initialize this ``ModuleLoader`` with a target top-level ``module``.
          Templates will be loaded under this top level module name, where
          directories are converted to packages and the template file has
          been converted to a Python module.

          :param module: Top-level Python package under which templates are
            kept. """

      from canteen.logic.cache import Caching

      if isinstance(module, basestring):
        try:
          module = importlib.import_module(module)
        except ImportError:
          pass
      self.cache, self.module = (
        Caching.spawn('tpl_%s' % module if (
          isinstance(module, basestring)) else module.__name__),
        module)

    def load(self, environment, filename, _globals=None):

      """ Load a compiled ``Jinja2`` template from an ``environment`` and
          template ``filename``.

          :param environment: Currently-active ``Jinja2`` template execution
            environment. Instance of :py:class:`jinja2.Environment`.

          :param filename: Filename for the final template to be served.
            Resolved to a Python module and executed to prepare the template
            routines.

          :param _globals: Global-level ``key=>value`` pairs (in a ``dict``) to
            be applied to the local rendering ``environment`` before render.

          :returns: Loaded :py:class:`jinja2.Template` object, an instance of
            the current ``environment``'s :py:attr:`template_class`. Prepared
            with bound ``_globals``, ``environment`` and ``blocks``. """

      _globals = _globals or {}

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
          _globals,
          mod.name,
          filename,
          blocks)

        # jinja2 internals
        t.root_render_func, t._module, t._debug_info, t._uptodate = (
          root,
          None,
          debug_info,
          lambda: True)

        self.cache.set(filename, t)
      return t

    def get_module(self, environment, template):

      """ Converts a template path to a package path and attempts import, or
          else raises ``Jinja2``'s :py:class:`TemplateNotFound`.

          :param environment: Currently-active ``Jinja2`` rendering environemnt.
            Instance of :py:class:`jinja2.Environment`.

          :param template: Full string filepath to the ``template`` desired.
            Converted to a Python-style dotted-path for import.

          :raises jinja2.TemplateNotFound: If the template in question could not
            be located or loaded properly in the current environment.

          :returns: Template module in question. """

      import jinja2

      # Convert the path to a module name.
      prefix, obj = (self.module.__name__ + '.' + (
        template.replace('/', '.').replace('-', '_')).rsplit('.', 1))
      prefix, obj = str(prefix), str(obj)

      try:
        return getattr(__import__(prefix, None, None, [obj]), obj)
      except (ImportError, AttributeError):
        raise jinja2.TemplateNotFound(template)


  class FileLoader(jinja2.FileSystemLoader):

    """ ``Jinja2`` template :py:class:`jinja2.Loader` subclass that loads
        template source files and indicates access to template sources. """

    has_source_access = True


@decorators.bind('template', namespace=False)
class Templates(logic.Logic):

  """ Provides logic related to templating for Canteen and Canteen-based apps.
      Currently supports ``Jinja2``, optionally with ``HAMLish``-flavored
      template syntax. """

  with runtime.Library('jinja2') as (library, jinja2):

    """ Prepares Jinja2 for integration with Canteen. """

    ## == Attributes == ##
    engine = jinja2  # we're using jinja :)
    default_extensions = property(lambda self: None)
    default_config = property(lambda self: {
      'optimized': True, 'autoescape': True})

    @staticmethod  # default syntax support method
    def _default_syntax(handler, environment_factory, j2config, config):

      """ Prepare the default template syntax, which is just ``Jinja2``'s
          regular template syntax.

          :param handler: Currently-active web handler. Always an instance of
            :py:class:`canteen.base.handler.Handler` or a subtype thereof.

          :param environment_factory: Callable that is charged with producing
            ``Jinja2`` :py:class:`jinja2.Environment` objects.

          :param j2config: ``Jinja2``-specific configuration, extracted from
            app config. These are *kwarg* parameters in ``Jinja2``'s docs for
            :py:class:`jinja2.Environment`.

          :param config: Reference to the full application config object, always
            an instance of :py:class:`canteen.util.config.Config`.

          :returns: Instance of :py:class:`jinja2.Environment`, prepared with
            ``Jinja2``'s default template syntax. """

      # factory environment
      return environment_factory(**j2config)

    syntax = _default_syntax

    # is there HAML syntax support?
    with runtime.Library('hamlish_jinja') as (haml_library, haml):

      """ Prepares HAMLish Jinja for integration with Canteen. """

      # we're using haml :)
      syntax_extension = (haml.HamlishExtension, haml.HamlishTagExtension)

      def _hamlish_syntax(self, handler, environment_factory, j2config, config):

        """ Prepare a ``HAMLish``-based tempmlate syntax, which is based on
            Ruby's *HAML*, but is extended/modified to be a bit more Pythonic
            and friendly to ``Jinja2``.

            :param handler: Currently-active web handler. Always an instance of
              :py:class:`canteen.base.handler.Handler` or a subtype thereof.

            :param environment_factory: Callable that is charged with producing
              ``Jinja2`` :py:class:`jinja2.Environment` objects.

            :param j2config: ``Jinja2``-specific configuration, extracted from
              app config. These are *kwarg* parameters in ``Jinja2``'s docs for
              :py:class:`jinja2.Environment`.

            :param config: Reference to the full application config object,
              always an instance of :py:class:`canteen.util.config.Config`.

            :returns: Instance of :py:class:`jinja2.Environment`, prepared with
              ``HAMLish``-based ``Jinja2`` template syntax. """

        # make environment first
        if 'extensions' not in j2config or not j2config.get('extensions'):

          # make sure standard j2 extensions are added
          j2config['extensions'] = [
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
            'jinja2.ext.do',
            'jinja2.ext.loopcontrols'
          ] + (self.default_extensions or [])

        # auto-add hamlish extension
        for ext in self.syntax_extension:
          if ext not in j2config['extensions']:
            j2config['extensions'].append(ext)

        # factory environment
        environment = environment_factory(**j2config)

        if config.debug:
          environment.hamlish_mode, environment.hamlish_debug = 'indented', True

        # apply config overrides
        if 'TemplateAPI' in config.config and 'haml' in (
          config.config['TemplateAPI']):

          for (config_item, target_attr) in (
            ('mode', 'hamlish_mode'),
            ('extensions', 'hamlish_file_extensions'),
            ('div_shortcut', 'hamlish_enable_div_shortcut')):

            if config_item in config.config['TemplateAPI']['haml']:
              setattr(*(
                environment,
                target_attr,
                config.config['TemplateAPI']['haml'][config_item]))

        return environment

      syntax = _hamlish_syntax

    def environment(self, handler, config):

      """ Prepare a new :py:class:`jinja2.Environment` object, for the purpose
          of rendering a template.

          :param handler: Currently-active web handler. Always an instance of
            :py:class:`canteen.base.handler.Handler` or a subtype thereof.

          :param config: Reference to top-level application configuration
            object. Always an instance of :py:class:`canteen.util.Config`.

          :raises RuntimeError: If no template root path is configured.

          :returns: Instance of :py:class:`jinja2.Environment`, prepared with
            settings and configuration from the current runtime environment. """

      # grab template path, if any
      output = config.get('TemplateAPI', {'debug': True})
      path = config.app.get('paths', {}).get('templates')
      jinja2_cfg = output.get('jinja2', self.default_config)

      if not path:
        # default path to cwd, and cwd + templates/, and cwd + templates/source
        cwd = os.getcwd()
        path = (
          os.path.join(cwd),
          os.path.join(cwd, 'templates'),
          os.path.join(cwd, 'templates', 'source'))

      # shim-in our loader system, unless it is overriden in config
      if 'loader' not in jinja2_cfg:

        if (output.get('force_compiled', False)) or (
          isinstance(path, dict) and 'compiled' in path and (not __debug__)):
          jinja2_cfg['loader'] = ModuleLoader(path['compiled'])

        else:
          jinja2_cfg['loader'] = FileLoader((
            path['source'] if isinstance(path, dict) else path))

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

    """ Clean yielded template content of preceding and trailing whitespace,
        ensure correct encoding, and chunk/yield efficiently.

        :param content: Content to sanitize. Must be ``str`` or ``unicode``.

        :param _iter: ``bool`` flag indicating we'd like to return a generator
          rather than buffer and return the content directly.

        :returns: ``callable`` generator if ``_iter`` is truthy, otherwise a
          buffered ``list`` of ``content`` that has been sanitized. """

    # content should be a list of content blocks
    content = [content] if not (
      isinstance(content, (tuple, list))) else content

    def sanitize():

      """ Inner sanitization generator. Closured and provided by ``sanitize``
          so that content can be yielded as a generator. """

      # iteratively sanitize the response
      for block in content: yield block.strip()

    if _iter: return sanitize()  # return wrapped iterator
    return [block for block in sanitize()]

  @decorators.bind('template.base_headers', wrap=property)
  def base_headers(self):

    """ Prepare a set of default (*base*) HTTP response headers to be included
        by-default on any HTTP response.

        :returns: ``list`` of ``tuples``, where each is a pair of ``key``-bound
          ``value`` mappings. Because HTTP headers can be repeated, a ``dict``
          is not usable in this instance. """

    return filter(lambda x: x and x[1], [
      ('Cache-Control', 'no-cache; no-store')])

  @decorators.bind('template.base_context', wrap=property)
  def base_context(self):

    """ Prepare a set of default (*base*) template context items that should
        always be available (as *globals*) in the ``Jinja2`` render context.

        :returns: ``dict`` of ``(key => value)`` pairs to be injected as globals
          into ``Jinja2``'s rendering context. """

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
      'getattr': getattr, 'setattr': setattr,
      'unicode': unicode, 'reversed': reversed,
      '__debug__': __debug__ and config.Config().debug,
      'isinstance': isinstance, 'issubclass': issubclass

    }

  @decorators.bind('template.base_filters', wrap=property)
  def base_filters(self):

    """ Prepare a set of default (*base*) template filters that should be made
        available (as *globals*) in the ``Jinja2`` render context.

        :returns: ``dict`` of ``(key => value)`` pairs to be injected as
          globally-available ``Jinja2`` filters (usable as ``val|filter`` in
          templates, which results in ``filter(val)``). """

    return {

      # Python Builtins (besides the Jinja2 defaults, which are _awesome_)
      'len': len, 'max': max, 'maximum': max, 'min': min, 'minimum': min,
      'avg': average, 'average': average,  # support for basic averages
      'json': json.dumps, 'tojson': json.dumps  # support for json

    }  # @TODO(sgammon): markdown/RST support?

  @decorators.bind('template.render')
  def render(self, handler, config, template, ctx, _direct=False):

    """ Top-level render function that handles template render flow from start
        to finish. Loads template and performs render flow.

        :param handler: Currently-active web handler. Always an instance of
          :py:class:`canteen.base.handler.Handler` or a subtype thereof.

        :param config: Reference to global application configuration. Always an
          instance of :py:class:`canteen.util.config.Config`.

        :param template: ``str``/``unicode`` relative filepath to the template
          source file we'd like to render and return. Sometimes converted to a
          Python module path or DB lookup, depending on the active ``Loader``.

        :param ctx: Merged context to apply to ``Jinja2``'s rendering
          environment. Always a ``dict``, sometimes could be an empty one.
          Values made available in templates under the keys they are listed at.

        :param _direct: ``bool`` flag indicating we'd like the render flow to
          fully buffer and return, rather than passing a generator that can be
          consumed step-by-step.

        :returns: inner ``generator`` made by :py:meth`TemplateAPI.sanitize``,
         if ``_direct`` was falsy, otherwise a ``list`` of chunked template
         content entries. """

    # render template & return content iterato)
    content = (
      self.environment(handler, config).get_template(template).render(**ctx))

    # if _direct is requested, sanitize and roll-up buffer immediately
    if _direct: return self.sanitize(content, _iter=False)

    # otherwise, buffer/chain iterators to produce a streaming response
    return self.sanitize(content)
