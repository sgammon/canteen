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

from __future__ import print_function

# stdlib
import os
import re
import sys
import json
import errno
import operator
import importlib
import py_compile

# os
from os import path, listdir

# base
from ..base import (logic,
                    handler)

# core & utils
from ..core import runtime
from ..util import decorators


## Constants
_RENDER_BUFFER = 7
_DEFAULT_MODULE_PREFIX = 'templates'
_DEFAULT_TEMPLATE_PATTERN = re.compile(
  r'^.*\.(html|js|haml|svg|css|sass|less|scss|coffee)$')
_FRAMEWORK_ROOT_PATH = (
  path.dirname(  # /canteen
    path.dirname(__file__)))  # /canteen/logic
_FRAMEWORK_TEMPLATE_ROOT = (
  path.join(_FRAMEWORK_ROOT_PATH, 'templates'))
_FRAMEWORK_TEMPLATE_SOURCES = (
  path.join(_FRAMEWORK_TEMPLATE_ROOT, 'source'))
_FRAMEWORK_TEMPLATES_COMPILED = (
  path.join(_FRAMEWORK_TEMPLATE_ROOT, 'compiled'))

## Globals
_conditionals = []

## Utility Lambdas
average = lambda x: reduce(operator.add, x) / len(x)
_dropext = lambda _path: path.splitext(_path)[0]
_make_module = lambda mod, prefix=_DEFAULT_MODULE_PREFIX: (
  '.'.join((prefix, mod)) if prefix else mod)
_make_import_statement = lambda module: 'from %s import *' % module
_make_module_path = lambda _path, root: (
  '/'.join(filter(bool, _dropext(_path).replace(root, '')
                                       .replace('.py', '')
                                       .split('/'))).replace('/', '.'))


with runtime.Library('jinja2', strict=True) as (library, jinja2):

  # jinja internals
  from jinja2 import nodes, compiler
  from jinja2.nodes import EvalContext
  from jinja2._compat import iteritems
  from jinja2.compiler import Frame, find_undeclared
  from jinja2.compiler import unoptimize_before_dead_code
  from jinja2.ext import with_, autoescape, do, loopcontrols

  DEFAULT_EXTENSIONS = [with_, autoescape, do, loopcontrols]


  def template_ast(self, node, frame=None):  # pragma: no cover

    """ Shim for Jinja2's default ``Jinja``-sytnax-to-Python AST converter.
        Wraps template code in a module-level ``run`` function that binds it
        to an instance of :py:class:`jinja2.Environment`.

        :param node: Current AST node.
        :param frame: Current code frame.
        :return: ``None``. """

    assert frame is None, 'no root frame allowed'
    eval_ctx = EvalContext(self.environment, self.name)

    from jinja2.runtime import __all__ as exported
    self.writeline('# -*- coding: utf-8 -*-')
    self.writeline('')
    self.writeline('from __future__ import division')
    self.writeline('from jinja2.runtime import ' + ', '.join(exported))
    if not unoptimize_before_dead_code:
        self.writeline('dummy = lambda *x: None')

    # if we want a deferred initialization we cannot move the
    # environment into a local name
    envenv = not self.defer_init and ', environment=environment' or ''

    # do we have an extends tag at all?  If not, we can save some
    # overhead by just not processing any inheritance code.
    have_extends = node.find(nodes.Extends) is not None

    # find all blocks
    for block in node.find_all(nodes.Block):
        if block.name in self.blocks:
            self.fail('block %r defined twice' % block.name, block.lineno)
        self.blocks[block.name] = block

    # find all imports and import them
    for import_ in node.find_all(nodes.ImportedName):
        if import_.importname not in self.import_aliases:
            imp = import_.importname
            self.import_aliases[imp] = alias = self.temporary_identifier()
            if '.' in imp:
                module, obj = imp.rsplit('.', 1)
                self.writeline('from %s import %s as %s' %
                               (module, obj, alias))
            else:
                self.writeline('import %s as %s' % (imp, alias))

    # add the load name
    self.writeline('name = %r' % self.name)

    # generate the deferred init wrapper
    self.writeline('def run(environment):', extra=1)
    self.indent()

    # generate the root render function.
    self.writeline('def root(context%s):' % envenv, extra=1)

    # process the root
    frame = Frame(eval_ctx)
    frame.inspect(node.body)
    frame.toplevel = frame.rootlevel = True
    frame.require_output_check = have_extends and not self.has_known_extends
    self.indent()
    if have_extends:
        self.writeline('parent_template = None')
    if 'self' in find_undeclared(node.body, ('self',)):
        frame.identifiers.add_special('self')
        self.writeline('l_self = TemplateReference(context)')
    self.pull_locals(frame)
    self.pull_dependencies(node.body)
    self.blockvisit(node.body, frame)
    self.outdent()

    # make sure that the parent root is called.
    if have_extends:
        if not self.has_known_extends:
            self.indent()
            self.writeline('if parent_template is not None:')
        self.indent()
        self.writeline('for event in parent_template.'
                       'root_render_func(context):')
        self.indent()
        self.writeline('yield event')
        self.outdent(2 + (not self.has_known_extends))

    # at this point we now have the blocks collected and can visit them too.
    for name, block in iteritems(self.blocks):
        block_frame = Frame(eval_ctx)
        block_frame.inspect(block.body)
        block_frame.block = name
        self.writeline('def block_%s(context%s):' % (name, envenv),
                       block, 1)
        self.indent()
        undeclared = find_undeclared(block.body, ('self', 'super'))
        if 'self' in undeclared:
            block_frame.identifiers.add_special('self')
            self.writeline('l_self = TemplateReference(context)')
        if 'super' in undeclared:
            block_frame.identifiers.add_special('super')
            self.writeline('l_super = context.super(%r, '
                           'block_%s)' % (name, name))
        self.pull_locals(block_frame)
        self.pull_dependencies(block.body)
        self.blockvisit(block.body, block_frame)
        self.outdent()

    self.writeline('blocks = {%s}' % ', '.join('%r: block_%s' % (x, x)
                                               for x in self.blocks),
                   extra=1)

    # add a function that returns the debug info
    self.writeline('debug_info = %r' % '&'.join('%s=%s' % x for x
                                                in self.debug_info))

    self.writeline('return (root, blocks, debug_info)')
    self.outdent()
    self.writeline('')

  compiler.CodeGenerator.visit_Template = template_ast


  class TemplateCompiler(object):

    """ Compiles ``Jinja2``-format templates into raw Python for faster
        execution, better optimization and more effective caching of template
        routines. """

    def __init__(self, module, sources, target, config,
                                prefix=_DEFAULT_MODULE_PREFIX,
                                debug=False):

      """ Initialize this ``TemplateCompiler``.

          :param module: Path to folder due to be used as the root for a new
            Python package containing both (recursively) ``compiled`` templates
            and ``sources``.

          :param sources: Path to folder of template source files, due to be
            (recursively) compiled into raw Python.

          :param target: Path to folder that should be filled with new Python
            files containing compiled template logic, built recursively from
            corresponding paths in ``sources``.

          :param config: Reference to application (or empty framework-level)
            configuration.

          :param prefix: Module prefix to prepend to compiled template
            imports.

          :param debug: Debug flag (``bool``) specifying whether we should
            output a bunch of noise about what's going on. Defaults to
            ``False``, in which case nothing is outputted. """

      self.module, self.sources, self.target, self.config, self.prefix = (
        module, sources, target, config, prefix)

      self.debug = debug

      # apply again
      compiler.CodeGenerator.visit_Template = template_ast

    @property
    def environment(self):

      """ Load a clean, throwaway ``Jinja2`` :py:class:`jinja2.Environment`
          instance, for the purpose of preparing compiled templates.

          :returns: Prepped instance of :py:class:`jinja2.Environment`. """

      return Templates().environment(handler.Handler(), self.config)

    @staticmethod
    def mkdir_p(fullpath):

      """ Recursively bring a directory path into existence. Similar to the Unix
          command ``mkdir -p``.

          :param fullpath: Path to recursively make directories for.

          :raises OSError: In the event of an unexpected error (such as a
            permissions or low-level storage error).

          :returns: Nothing. """

      try:
        os.makedirs(fullpath)
      except OSError as e:
        if e.errno == errno.EEXIST and path.isdir(fullpath):
          pass
        else:  # pragma: no cover
          raise

    @classmethod
    def framework(cls, config=None, run=False):

      """ Class-level shortcut to spawn a ``TemplateCompiler`` instance that is
          pre-configured to build builtin framework templates.

          :param config: Instance of :py:class:`canteen.util.config.Config`
            that should be used when compiling templates.

          :param run: ``bool`` flag indicating that the compiler should be run
            automatically, instead of returned. Defaults to ``False``.

          :returns: Instance of ``TemplateCompiler``. """

      from canteen.util import config as configutil

      # create `compiled` root folder, if necessary
      if not path.isdir(_FRAMEWORK_TEMPLATES_COMPILED):  # pragma: no cover
        cls.mkdir_p(_FRAMEWORK_TEMPLATES_COMPILED)

      compiled = cls(_FRAMEWORK_TEMPLATE_ROOT,
                     _FRAMEWORK_TEMPLATE_SOURCES,
                     _FRAMEWORK_TEMPLATES_COMPILED,
                     config or configutil.Config(),
                     'canteen.templates')
      if run: return compiled()
      return compiled

    def compile(self, environment, source, destination,
                                              encoding='utf-8',
                                              base_dir=''):

      """ Compile an individual ``Jinja2``-formatted template into raw Python,
          using a slightly customized version of the standard Jinja template
          compiler.

          :param environment: Instance of :py:class:`jinja2.Environment` to use
            for compiling the actual template sources.

          :param source: Path to source directory that is due to be recursively
            compiled into raw Python at ``destination``.

          :param destination: Destination directory that is due to be filled
            with compiled raw Python templates.

          :param encoding: Default encoding when reading template ``source``
            files and writing template ``destination`` files.

          :param base_dir: Base directory path to be removed from the beginning
            of compiled template names.

          :raises ValueError: If a template name collides with a folder name
            and so cannot be used in a compiled fashion, since they would
            generate ambiguous import paths in Python.

          :returns: ``list`` of new template import paths that should work if
            ``destination`` is in the current interpreter's ``sys.path``. """

      with open(source) as template:

        name = source.replace(base_dir, '')  # remove base path from name

        try:
          raw = environment.compile(template.read().decode(encoding), **{
            'name': name,
            'filename': name,
            'raw': True,
            'defer_init': True})

        except jinja2.TemplateSyntaxError:  # pragma: no cover
          print("!!! Syntax error in file '%s'. Compilation failed. !!!" % (
            str(source)))
          exit(1)

        target_name, ext = path.splitext(destination)
        if path.isdir(target_name):  # pragma: no cover
          raise ValueError('Template name conflict: `%s` is a directory,'
                           ' so %s%s cannot exist as an independent'
                           ' template file.' % (name, name, ext))

        self.mkdir_p((path.join(*tuple(destination.split('/')[0:-1]))))

        with open('.'.join((target_name, 'py')), 'w') as target:
          target.write(raw)
      return destination

    def compile_dir(self, source, destination,
                          base_dir='',
                          pattern=_DEFAULT_TEMPLATE_PATTERN,
                          encoding='utf-8',
                          fill_init=True):

      """ Recursively compile a directory of ``Jinja2``-formatted templates to
          raw Python source code.

          :param source: Source directory to compile from.

          :param destination: Destination directory to write compiled Python
            template files to.

          :param base_dir: Base directory that contains both ``source`` and
            ``destination``, if any. Manages canteen-style ``__init__.py``
            file.

          :param pattern: String regex pattern to scan files against in the
            ``source`` directory. Matching filenames are considered to be
            ``Jinja2``-format templates and will be marked for compilation.

          :param encoding: Default encoding when reading template ``source``
            files and writing template ``destination`` files.

          :param fill_init: Fill out an proper ``__init__.py``, aggressively
            importing submodules.

          :returns: Full (recursively-built) list of import paths generated
            during the compilation routine. """

      if not destination.replace(base_dir, '') == '':
        destination = path.join(base_dir, '/'.join(
          destination.replace(base_dir, '').replace('-', '_').split('/')[1:]))

      _import_paths = []

      if path.isdir(destination):  # pragma: no cover
        init = path.join(destination, '__init__.py')
        if not path.exists(init):
          open(init, 'w').close()

      for filename in listdir(source):
        source_name, destination_name = (
          path.join(source, filename),
          path.join(destination, filename.replace('-', '_')))

        # @TODO(sgammon): compiling file
        if self.debug:  # pragma: no cover
          print('Compiling %s...' % filename)

        if path.isdir(source_name):
          self.mkdir_p(destination_name)
          _import_paths += self.compile_dir(
              source_name,
              destination_name,
              base_dir,
              encoding=encoding)

        elif path.isfile(source_name) and (
            re.match(pattern, filename)):  # pragma: no cover

          # make sure directories are there
          if not path.isdir(path.dirname(source_name)):
            self.mkdir_p(path.dirname(source_name))

          new_target = _make_module_path(
            self.compile(self.environment, source_name, destination_name,
                          encoding=encoding,
                          base_dir=base_dir), base_dir)

          _import_paths.append(_make_module(new_target, self.prefix))

          file_path, file_name = tuple(destination_name.rsplit('/', 1))
          source_path = path.join(file_path, '.'.join((
            file_name.rsplit('.', 1)[0], 'py')))

          precompiled_path = path.join(file_path, '.'.join((
            file_name.rsplit('.', 1)[0], 'pyc' if (
              sys.flags.optimize) else 'pyo')))

          try:
            py_compile.compile(source_path, precompiled_path)
          except Exception:
            print("Failed to precompile: '%s'... Skipping..." % source_path)

        elif path.isfile(source_name) and not (
            re.match(pattern, filename)):  # pragma: no cover
          with open(destination_name, 'wb') as staticwrite:
            with open(source_name, 'rb') as staticread:
              staticwrite.write(staticread.read())

      if path.isdir(destination) and fill_init:
        with open(path.join(destination, '__init__.py'), 'w') as init:
          map(lambda line: init.write(line + "\n"), (
            '# -*- coding: utf-8 -*-',
            '',
            '"""',
            '',
            '   compiled templates: %s' % _make_module_path(*(
                                                      destination, base_dir)),
            '',
            '"""',
            '',
            '# subtemplates',
            "\n".join(map(_make_import_statement, _import_paths)),
            ''))

      return _import_paths

    def __call__(self, **kw):

      """ Defer calls on ``TemplateCompiler`` objects to :py:meth:`compile_dir`.

          :param kw: Keyword arguments to pass to ``compile_dir``.
          :returns: Whatever ``compile_dir`` decides to return. """

      return self.compile_dir(*(self.sources, self.target, self.module), **kw)


  class ModuleLoader(jinja2.ModuleLoader):

    """ ``Jinja2`` :py:class:`TemplateLoader`, responsible for resolving Python-
        optimized template routines. When ``Jinja2`` templates are compiled to
        raw Python, this is the loader that is responsible for
        importing/executing/preparing responses from those templates. """

    cache = None  # cache of modules loaded
    module = None  # main module
    has_source_access = False  # from jinja's internals

    def __init__(self, module='templates', strict=False):

      """ Initialize this ``ModuleLoader`` with a target top-level ``module``.
          Templates will be loaded under this top level module name, where
          directories are converted to packages and the template file has
          been converted to a Python module.

          Canteen extends *Jinja2's* builtin ``ModuleLoader`` to work with a
          slightly-customized form of compiled templates, where the compiled
          template content is wrapped in a module-level callable that binds it
          to the current ``environment``. This specialized compiler is shipped
          with Canteen at :py:mod:`canteen.logic.template.Compiler`.

          :param module: Top-level Python package to load from. Essentially
            treated as a module prefix, added before any template paths are
            converted to dotted Python module paths. Thus, a value of
            ``templates`` (the default) paired with a later template source
            request for `pages/about.html` would result in an import call for
            the module path ``templates.pages.about``.

          :param strict: Whether to silently or loudly fail if the given
            ``module`` could not be loaded. ``bool`` that defaults to ``False``,
            meaning we should fail silently and later fail all template requests
            with a ``jinja2.TemplateNotFound`` (until the import succeeds, as it
            will be retried each time). ``True`` will raise an ``ImportError``
            from this function if the module is invalid.

          :raises ImportError: If ``strict`` is set to ``True`` and the given
            ``module`` is invalid or could not be loaded. """

      from canteen.logic.cache import Caching

      if isinstance(module, basestring):
        try:
          module = importlib.import_module(module)
        except ImportError:
          # @TODO(sgammon): log if not found
          if strict: raise
          raise jinja2.TemplateNotFound('Failed to locate compiled template'
                                        ' %s. %s' % (module, (
                                        'Strict mode was active.' if (
                                        strict) else (
                                          'Strict mode was not active.'))))

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

      if isinstance(self.module, basestring):  # pragma: no cover
        self.module = importlib.import_module(self.module)

      filename, ext = path.splitext(filename.strip('/'))

      t = self.cache.get(filename)
      if not t:
        # Store module to avoid unnecessary repeated imports.
        mod = self.get_module(filename)

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

    def get_module(self, template):

      """ Converts a template path to a package path and attempts import, or
          else raises ``Jinja2``'s :py:class:`TemplateNotFound`.

          :param template: Full string filepath to the ``template`` desired.
            Converted to a Python-style dotted-path for import.

          :raises jinja2.TemplateNotFound: If the template in question could not
            be located or loaded properly in the current environment.

          :returns: Template module in question. """

      import jinja2

      fullpath = self.module.__name__.split('.') + template.split('/')
      prefix, obj = '.'.join(fullpath[:-1]), fullpath[-1]

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
    env = library.load('environment')  # load environment tools
    render_buffer_size = _RENDER_BUFFER  # render statements to buffer at a time
    default_extensions = property(lambda self: DEFAULT_EXTENSIONS)
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

    def environment(self, _handler, config):

      """ Prepare a new :py:class:`jinja2.Environment` object, for the purpose
          of rendering a template.

          :param _handler: Currently-active web handler. Always an instance of
            :py:class:`canteen.base.handler.Handler` or a subtype thereof.

          :param config: Reference to top-level application configuration
            object. Always an instance of :py:class:`canteen.util.Config`.

          :raises RuntimeError: If no template root path is configured.

          :returns: Instance of :py:class:`jinja2.Environment`, prepared with
            settings and configuration from the current runtime environment. """

      # grab template path, if any
      output = config.get('TemplateAPI', {'debug': True})
      jinja2_cfg = output.get('jinja2', self.default_config)

      _path = None
      if isinstance(config.app, dict):
        _path = config.app.get('paths', {}).get('templates', None)

      if not _path:
        # default path to cwd, and cwd + templates/, and cwd + templates/source
        cwd = os.getcwd()
        _path = (path.join(cwd),
                 path.join(cwd, 'templates'),
                 path.join(cwd, 'templates', 'source'))

      # shim-in our loader system, unless it is overriden in config
      if 'loader' not in jinja2_cfg:

        if output.get('force_compiled', False) or (
          isinstance(_path, dict) and 'compiled' in _path):

          if output.get('force_compiled', False):
            jinja2_cfg['loader'] = ModuleLoader(_path['compiled'], strict=True)
          else:
            choices = []
            if isinstance(_path, dict) and 'compiled' in _path:
              try:
                choices.append(ModuleLoader(_path['compiled']))
              except jinja2.TemplateNotFound:  # pragma: no cover
                pass  # no compiled template root at all

            if (isinstance(_path, dict) and 'source' in _path or (
                  isinstance(_path, basestring))):
              choices.append(FileLoader(_path['source'] if (
                             isinstance(_path, dict)) else _path))

            if not choices:  # pragma: no cover
              raise RuntimeError('No template path configured.')

            jinja2_cfg['loader'] = jinja2.ChoiceLoader(choices)

        else:
          jinja2_cfg['loader'] = FileLoader((
            _path['source'] if isinstance(_path, dict) else _path))

        if 'loader' not in jinja2_cfg:  # pragma: no cover
          raise RuntimeError('No configured template source path.')

      # make our new environment
      j2env = self.syntax(_handler, self.engine.Environment, jinja2_cfg, config)

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

  @classmethod
  def sanitize(cls, content, _iter=True):

    """ Clean yielded template content of preceding and trailing whitespace,
        ensure correct encoding, and chunk/yield efficiently.

        :param content: Content to sanitize. Must be ``str`` or ``unicode``.

        :param _iter: ``bool`` flag indicating we'd like to return a generator
          rather than buffer and return the content directly.

        :returns: ``callable`` generator if ``_iter`` is truthy, otherwise a
          buffered ``list`` of ``content`` that has been sanitized. """

    # content should be a list of content blocks
    content = [content] if not (
      isinstance(content, (tuple, list, cls.env.TemplateStream))) else content

    def sanitize():

      """ Inner sanitization generator. Closured and provided by ``sanitize``
          so that content can be yielded as a generator. """

      # iteratively sanitize the response
      for _block in content: yield _block.strip()

    if _iter: return sanitize()  # return wrapped iterator
    return [block for block in sanitize()]

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
      'isinstance': isinstance, 'issubclass': issubclass}

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
    tpl = (
      self.environment(handler, config).get_template(template))

    # if _direct is requested, sanitize and roll-up buffer immediately
    if _direct: return self.sanitize(tpl.render(**ctx), _iter=False)

    gen = tpl.stream(**ctx)
    gen.enable_buffering(size=self.render_buffer_size)

    # otherwise, buffer/chain iterators to produce a streaming response
    return self.sanitize(gen)
