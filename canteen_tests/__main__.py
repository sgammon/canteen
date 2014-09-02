# -*- coding: utf-8 -*-

"""

  test runner
  ~~~~~~~~~~~

  discovers canteen's tests, then runs them.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""


if __debug__:  # pragma: no cover

  # stdlib & canteen
  import sys, os


  if __name__ == '__main__' and (
        'CANTEEN_TESTING' not in os.environ):  # pragma: no cover
    import nose
    sys.exit(int(nose.run()))
