# -*- coding: utf-8 -*-

"""

  template logic tests
  ~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import pprint
import inspect

# testing tools
from canteen import test

# template logic and base handler
from canteen.util import config
from canteen.base import handler
from canteen.logic import template

try:
  import jinja2
except ImportError:  # pragma: no cover
  jinja2 = None
  print('Warning! Jinja2 not found. Template logic tests will be skipped.')

try:
  import hamlish_jinja
except ImportError:  # pragma: no cover
  hamlish_jinja = None
  print('Warning! Hamlish Jinja not found. Custom template'
        ' syntax tests will be skipped.')


if jinja2:


  class TemplateCompilerTests(test.FrameworkTest):

    """ Tests builtin :py:class:`canteen.logic.TemplateCompiler` class, which
        compiles Jinja2-formatted templates to raw Python. """

    def test_construct(self):

      """ Test constructing a new `TemplateCompiler` """

      t = template.TemplateCompiler(*(
        None, None, None, config.Config(), 'canteen.templates'))
      assert t.module == template._FRAMEWORK_TEMPLATE_ROOT
      assert t.sources == template._FRAMEWORK_TEMPLATE_SOURCES
      assert t.target == template._FRAMEWORK_TEMPLATES_COMPILED
      return t

    def test_environment(self):

      """ Test constructing a throwaway environment with `TemplateCompiler` """

      t = self.test_construct()
      assert isinstance(t.environment, jinja2.Environment)

    def test_context(self):

      """ Test patching Jinja2's compiler internals with `TemplateCompiler` """

      t = self.test_construct()
      assert not t.shim_active

      with t:
        assert t.shim_active

      assert not t.shim_active

    def test_compile(self):

      """ Test compiling canteen's builtin template sources """

      t = self.test_construct()
      t()
      return t


  class ModuleLoaderTests(test.FrameworkTest):

    """ Tests builtin :py:class:`jinja2.Loader` subtype `ModuleLoader`, which
        provides logic to load template sources via pure-Python modules, as is
        the case if ``canteen``'s custom template compiler is in use. """

    @property
    def logic(self):

      """ Utility property to return a new reference to Canteen's builtin
          ``Templates`` logic.

          :returns: Instance of :py:class:`canteen.logic.templates.Templates`
            for testing purposes. """

      return template.Templates()

    @property
    def environment(self):

      """ Utility property to return a throwaway *Jinja2* template rendering
          environment.

          :returns: Instance of :py:class:`jinja2.Environment`. """

      return self.logic.environment(*(
        handler.Handler({'sample': 'hi'}, lambda: True), config.Config()))

    def test_construct(self):

      """ Test constructing a template source `ModuleLoader` """

      l = template.ModuleLoader('canteen.templates.compiled')
      assert not l.has_source_access
      return l

    def test_construct_nonstrict_invalid(self):

      """ Test constructing an invalid `ModuleLoader` """

      template.ModuleLoader('hahaidonotexistfuckyou', strict=False)

    def test_construct_strict_invalid(self):

      """ Test constructing an invalid `ModuleLoader` """

      with self.assertRaises(ImportError):
        template.ModuleLoader('hahaidonotexistfuckyou', strict=True)

    def test_load_builtin(self):

      """ Test loading builtin Canteen templates via `ModuleLoader` """

      compiler = template.TemplateCompiler(*(
        None, None, None, config.Config(), 'canteen.templates'))
      t = template.ModuleLoader('canteen.templates.compiled', strict=True)
      m = t.load(compiler.environment, 'base.html')
      assert m

      n = t.load(compiler.environment, 'base.html')
      assert n and m is n
      assert type(n) is type(m)

  # @TODO(sgammon): ahahaha finish these

    def test_load_valid(self):

      """ Test loading template sources through a `ModuleLoader` """

      l = self.test_construct()
      assert l
      t = l.load(self.environment, 'base.html')
      assert t

    def test_load_invalid(self):

      """ Test loading an invalid template file through a `ModuleLoader` """

      l = self.test_construct()
      with self.assertRaises(jinja2.TemplateNotFound):
        l.load(self.environment, 'hahahaha.html')


  class TemplateLogicTests(test.FrameworkTest):

    """ Tests builtin framework logic and integration points for rendering
        template sources into response content. """

    def _spawn_handler(self):

      """ Spawn a throwaway utility handler. """

      return handler.Handler({}, lambda: None)

    def _spawn_config(self, _config={}, app={}):

      """ Spawn a throwaway app config, optionally overlaying ``overlay``.

          :param _config: Dictionary of updates to temporarily apply to the
            resulting ``config`` block.

          :param app: Dictionary of updates to temporarily apply to the
            resulting ``app`` block.

          :returns: Overridden app config object with values from ``overlay``,
            if any. """

      c = config.Config()
      _cfg = c.blocks.get('config', {})
      _cfg['TemplateAPI'] = (_cfg.get('TemplateAPI') or {})
      _cfg['TemplateAPI'].update(_config)

      _app = c.blocks.get('app', {})
      _app.update(app)
      c.blocks['config'] = _cfg
      c.blocks['app'] = _app

      return c

    def test_construct(self):

      """ Test basic construction of builtin `Template` logic """

      return template.Templates()

    def test_provide(self):

      """ Test that `Template` logic is provided via the DI pool """

      l = handler.Handler({}, lambda: None)
      assert l.template

    def test_jinja2_integration(self):

      """ Test that `Template` integration with `Jinja2` is supported """

      t = self.test_construct()
      assert t.engine is jinja2

    def test_syntax(self):

      """ Test that `Template` syntax extensions properly load and mount """

      t = self.test_construct()
      assert hasattr(t, 'syntax')

      # test builtin default syntax
      default = t._default_syntax(
        None, jinja2.Environment, {}, config.Config())

      assert isinstance(default, jinja2.Environment)

    def test_environment_custom_syntax(self):

      """ Test construction of a `Jinja2` environment with custom syntax """

      if hamlish_jinja:

        env = self.test_construct().syntax(
          self._spawn_handler(), jinja2.Environment, {}, self._spawn_config({
            'haml': {
              'mode': 'debug'}}))

        assert isinstance(env, jinja2.Environment)

    def test_environment_syntax_override(self):

      """ Test overriding Jinja2's standard syntax points """

      t = self.test_construct()
      e = t.environment(self._spawn_handler(), self._spawn_config({
          'syntax': {
            'block': ('[[', ']]')}}))

      assert isinstance(e, jinja2.Environment)
      assert e.block_start_string == '[['
      assert e.block_end_string == ']]'

    def test_spawn_loader_source(self):

      """ Test spawing a new `FileLoader` for loading template sources """

      t = self.test_construct()
      e = t.environment(self._spawn_handler(), self._spawn_config(app={
        'paths': {
          'templates': {
            'source': template._FRAMEWORK_TEMPLATE_SOURCES}}}))

      assert e and isinstance(e, jinja2.Environment)

      e = t.environment(self._spawn_handler(), self._spawn_config(app={
        'paths': {
          'templates': template._FRAMEWORK_TEMPLATE_SOURCES}}))

      assert e and isinstance(e, jinja2.Environment)

    def test_spawn_loader_forcecompiled(self):

      """ Test spawning a `ModuleLoader` to load Python-compiled templates """

      t = self.test_construct()
      e = t.environment(self._spawn_handler(), self._spawn_config({
          'debug': True,
          'force_compiled': True}, app={
            'paths': {
              'templates': {
                'source': template._FRAMEWORK_TEMPLATE_SOURCES,
                'compiled': 'canteen.templates.compiled'}}}))

      assert e and isinstance(e, jinja2.Environment)

    def test_spawn_loader_both(self):

      """ Test spawning a `ChoiceLoader` to use source + compiled templates """

      t = self.test_construct()
      e = t.environment(self._spawn_handler(), self._spawn_config(app={
        'paths': {
          'templates': {
            'source': template._FRAMEWORK_TEMPLATE_SOURCES,
            'compiled': 'canteen.templates.compiled'}}}))

      assert e and isinstance(e, jinja2.Environment)
      assert e.loader

    def test_sanitize_buffered(self):

      """ Test buffered sanitization of template content """

      t = self.test_construct()
      result = t.sanitize('  <b> blab </b>  ', False)
      assert result and len(result)
      assert result[0] == '<b> blab </b>'

    def test_sanitize_generator(self):

      """ Test streaming sanitization of template content """

      t = self.test_construct()
      result = t.sanitize('  <b> blab </b>  ')
      assert inspect.isgenerator(result)
      items = [i for i in result]
      assert items and len(items)
      assert items[0] == '<b> blab </b>'

    def test_base_context_factory(self):

      """ Test that base context can be provided by `Templates` logic """

      l = self.test_construct()
      context = l.base_context

      for item in ('all', 'any', 'int', 'str',
                   'len', 'map', 'max', 'min',
                   'enumerate', 'zip', 'bool',
                   'list', 'dict', 'tuple', 'range',
                   'round', 'slice', 'xrange', 'filter',
                   'reduce', 'sorted', 'getattr', 'setattr',
                   'unicode', 'reversed', '__debug__',
                   'isinstance', 'issubclass'):
        assert item in context, (
          "expected to find item '%s' in base template context"
          " but item failed to resolve in context: %s" % (
            item, pprint.pprint(context)))

    def test_builtin_render_direct(self):

      """ Test direct template render path with `Templates.render` """

      l = self.test_construct()
      result = l.render(self._spawn_handler(),
                        self._spawn_config(app={
                          'paths': {
                            'templates': {
                              'source': template._FRAMEWORK_TEMPLATE_SOURCES,
                              'compiled': 'canteen.templates.compiled'}}}),

                        'base.html',
                        {'var': 'hi'},
                        _direct=True)

      assert isinstance(result, list)
      assert '<html></html>' in result[0]

    def test_builtin_render_indirect(self):

      """ Test indirect template render path with `Templates.render` """

      l = self.test_construct()
      result = l.render(self._spawn_handler(),
                        self._spawn_config(app={
                          'paths': {
                            'templates': {
                              'source': template._FRAMEWORK_TEMPLATE_SOURCES,
                              'compiled': 'canteen.templates.compiled'}}}),
                        'base.html',
                        {'var': 'hi'})

      assert inspect.isgenerator(result)
      chunks = [i for i in result]
      assert '<html></html>' in chunks[0]

      snippet = l.render(self._spawn_handler(),
                        self._spawn_config(app={
                          'paths': {
                            'templates': {
                              'source': template._FRAMEWORK_TEMPLATE_SOURCES,
                              'compiled': 'canteen.templates.compiled'}}}),
                          'snippets/test.html',
                          {'var': 'hi'})

      assert inspect.isgenerator(snippet)
      chunks = [i for i in snippet]
      assert '<b></b>' in chunks[0]

    def test_environment_factory_with_loader(self):

      """ Test construction of `Jinja2` environments with different loaders """

      t = self.test_construct()
      e = t.environment(self._spawn_handler(), self._spawn_config({
            'jinja2': {'loader': 5}}))

      assert isinstance(e, jinja2.Environment)
      assert e.loader == 5
