# -*- coding: utf-8 -*-

'''

  canteen: core output API
  ~~~~~~~~~~~~~~~~~~~~~~~~

  exposes a core API for interfacing with template engines
  like :py:mod:`Jinja2`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# core API & util
from . import CoreAPI
from canteen.util import decorators


@decorators.bind('output')
class OutputAPI(CoreAPI):

  '''  '''

  pass
