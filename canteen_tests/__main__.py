# -*- coding: utf-8 -*-

'''

  canteen: test runner
  ~~~~~~~~~~~~~~~~~~~~

  discovers canteen's tests, then runs them.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
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

    import nose
    sys.exit(int(nose.run()))
