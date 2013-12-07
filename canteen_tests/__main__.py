# -*- coding: utf-8 -*-

'''

  canteen test runner
  ~~~~~~~~~~~~~~~~~~~

  discovers canteen's tests, then runs them.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''


if __debug__:

  # stdlib & canteen
  import os
  import sys
  import canteen
  import canteen.test

  if __name__ == '__main__':

    # run 'em yo
    #os.environ['TEST_REIMPORT'] = '1'
    #canteen.test.clirunner(sys.argv[1:], root=os.path.dirname(__file__))

    import nose
    sys.exit(int(nose.run()))
