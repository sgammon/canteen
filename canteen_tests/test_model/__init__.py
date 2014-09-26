# -*- coding: utf-8 -*-

"""

  model tests
  ~~~~~~~~~~~

  tests canteen's data modelling layer.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

if __debug__:

  # stdlib
  import os

  # canteen tests
  from canteen.test import FrameworkTest


  ## ModelExportTests
  class ModelExportTests(FrameworkTest):

    """ Tests objects exported by `model`. """

    def test_concrete(self):

      """ Test that we can import concrete classes. """

      try:
        from canteen import model
        from canteen.model import Key
        from canteen.model import Model
        from canteen.model import Property
        from canteen.model import AbstractKey
        from canteen.model import AbstractModel

      except ImportError:  # pragma: no cover
        return self.fail("Failed to import concrete classes exported by Model.")

      else:
        self.assertTrue(Key)  # must export Key
        self.assertTrue(Model)  # must export Model
        self.assertTrue(Property)  # must export Property
        self.assertTrue(AbstractKey)  # must export AbstractKey
        self.assertTrue(AbstractModel)  # must export AbstractModel
        self.assertIsInstance(model, type(os))  # must be a module (lol)


  __all__ = (
      'test_graph',
      'test_key',
      'test_meta',
      'test_model',
      'test_query')
