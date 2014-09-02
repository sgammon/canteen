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

  def test_runscript(self):

    """ Test basic functionality of `canteen.__main__` """

    from canteen import __main__
    assert hasattr(__main__, 'walk')
    assert hasattr(__main__, 'run')
    assert hasattr(__main__, 'app')

  def test_walk_and_main(self):

    """ Test package walking functionality from `canteen.__main__` """

    from canteen import __main__
    from canteen.util import walk

    assert __main__.walk is walk

    # walk packages
    walk()

    # make sure testing __main__ is at least importable
    from canteen_tests import __main__

  def test_spawn(self):

    """ Test mechanics of top-level `spawn` """

    from canteen import spawn
    from canteen.core import runtime

    x = spawn(None, {})

    assert isinstance(x, runtime.Runtime)

  def test_framework_all(self):

    """ Test for expected Framework-level exports """

    for attr in ('__all__',
                  'base', 'core', 'logic', 'model', 'rpc', 'runtime', 'util',
                  'Library', 'Logic', 'Page', 'Service', 'Model', 'Vertex',
                  'Edge', 'Key'):
      assert hasattr(canteen, attr), (
        "failed to resolve expected framework export: '%s'." % attr)
