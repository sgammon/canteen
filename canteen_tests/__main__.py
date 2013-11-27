# -*- coding: utf-8 -*-

'''

  canteen test runner
  ~~~~~~~~~~~~~~~~~~~

  discovers canteen's tests, then runs them.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''


if __debug__:

  # stdlib & canteen
  import sys
  import canteen
  import canteen.test

  # canteen's tests
  try:
    from canteen_tests import *
  except ImportError:
    print "Couldn't load tests. Make sure `canteen_tests` is installed."
    sys.exit(1)

  # run 'em yo
  canteen.test.clirunner(sys.argv[1:])
