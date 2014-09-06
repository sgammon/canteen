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

# testing tools
from canteen import test

# template logic and base handler
from canteen.util import config
from canteen.base import handler
from canteen.logic import template

try:
  import jinja2
except ImportError:
  jinja2 = None
  print('Warning! Jinja2 not found. Template logic tests will be skipped.')




if jinja2:


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

      l = template.ModuleLoader('canteen.templates')
      assert not l.has_source_access
      return l

    def test_construct_nonstrict_invalid(self):

      """ Test constructing an invalid `ModuleLoader` """

      template.ModuleLoader('hahaidonotexistfuckyou', strict=False)

    def test_construct_strict_invalid(self):

      """ Test constructing an invalid `ModuleLoader` """

      with self.assertRaises(ImportError):
        template.ModuleLoader('hahaidonotexistfuckyou', strict=True)


  # @TODO(sgammon): ahahaha finish these

  '''
    def test_load_valid(self):

      """ Test loading template sources through a `ModuleLoader` """

      l = self.test_construct()
      assert l
      t = l.load(self.environment, 'base.html')
      assert t

    def test_load_invalid(self):

      """ Test loading an invalid template file through a `ModuleLoader` """

      l = self.test_construct()

    def test_module_cache(self):

      """ Test repeated source loads through a `ModuleLoader` """

      pass

    def test_get_module(self):

      """ Test the internal method `ModuleLoader.get_module` """

      pass


  class TemplateLogicTests(test.FrameworkTest):

    """ Tests builtin framework logic and integration points for rendering
        template sources into response content. """

    def test_provide(self):

      """ Test that `Template` logic is provided via the DI pool """

      pass

    def test_jinja2_integration(self):

      """ Test that `Template` integration with `Jinja2` is supported """

      pass

    def test_syntax(self):

      """ Test that `Template` syntax extensions properly load and mount """

      pass

    def test_environment_factory(self):

      """ Test that `Template` can factory `Jinja2` template environments """

      pass

    def test_environment_factory_with_loader(self):

      """ Test construction of `Jinja2` environments with different loaders """

      pass

    def test_environment_factory_default_template_path(self):

      """ Test construction of a `Jinja2` environment without a default root """

      pass

    def test_environment_base_syntax(self):

      """ Test construction of a `Jinja2` environment with default syntax """

      pass

    def test_environment_custom_syntax(self):

      """ Test construction of a `Jinja2` environment with custom syntax """

      pass

    def test_sanitize_buffered(self):

      """ Test buffered sanitization of template content """

      pass

    def test_sanitize_generator(self):

      """ Test streaming sanitization of template content """

      pass
    '''

