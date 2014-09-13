# -*- coding: utf-8 -*-

"""

  init tests
  ~~~~~~~~~~

  tests things at the top-level package init for canteen.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# canteen
import canteen
from canteen import test


class BaseFrameworkTests(test.FrameworkTest):

  """ Tests basic framework details. """

  def test_framework_all(self):

    """ Test for expected Framework-level exports """

    for attr in ('__all__',
                  'base', 'core', 'logic', 'model', 'rpc', 'runtime', 'util',
                  'Library', 'Logic', 'Page', 'Service', 'Model', 'Vertex',
                  'Edge', 'Key'):
      assert hasattr(canteen, attr), (
        "failed to resolve expected framework export: '%s'." % attr)
