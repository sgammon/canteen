# -*- coding: utf-8 -*-

"""

  model meta tests
  ~~~~~~~~~~~~~~~~

  tests metacomponents of canteen's model layer.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import inspect

# canteen model API
from canteen import model
from canteen.model import adapter
from canteen.model import MetaFactory

# canteen tests
from canteen.test import FrameworkTest


## MetaFactoryTests
class MetaFactoryTests(FrameworkTest):

  """ Tests `model.MetaFactory`. """

  def test_abstract_factory(self):

    """ Test that `MetaFactory` is only usable abstractly. """

    # constructing metafactory should raise an ABC exception
    self.assertTrue(inspect.isabstract(MetaFactory))
    with self.assertRaises(NotImplementedError):
      MetaFactory()

  def test_abstract_enforcement(self):

    """ Test abstraction enforcement on `MetaFactory` """

    class InsolentClass(MetaFactory):

      """ Look at me! I extend without implementing. The nerve! """

      # intentionally not defined: def classmethod(initialize())
      pass

    with self.assertRaises(TypeError):
      InsolentClass(*(InsolentClass.__name__,
                      (MetaFactory, type),
                      dict([
                        (k, v) for k, v in InsolentClass.__dict__.items()])))

  def test_resolve_adapters(self):

    """ Test that `MetaFactory` resolves adapters correctly """

    # test that resolve exists
    self.assertTrue(inspect.ismethod(MetaFactory.resolve))
    self.assertIsInstance(MetaFactory.resolve(*(model.Model.__name__,
                                                model.Model.__bases__,
                                                model.Model.__dict__,
                                                False)), tuple)

    self.assertIsInstance(MetaFactory.resolve(*(model.Model.__name__,
                                                model.Model.__bases__,
                                                model.Model.__dict__,
                                                True)), adapter.ModelAdapter)
