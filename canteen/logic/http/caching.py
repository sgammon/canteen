# -*- coding: utf-8 -*-

'''

  canteen: HTTP caching logic
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core runtime
from canteen.base import logic
from canteen.core import runtime

# canteen utils
from canteen.util import decorators


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):


  @decorators.bind('http.caching')
  class Caching(logic.Logic):

    '''  '''

    pass


  __all__ = (
    'Caching',
  )
