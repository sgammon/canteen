# -*- coding: utf-8 -*-

'''

  canteen HTTP cookie-related logic
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core runtime
from canteen.base import logic
from canteen.core import runtime

# canteen utils
from canteen.util import decorators

# core session API
from canteen.core.api.session import SessionEngine


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):


  @decorators.bind('cookies')
  class Cookies(logic.Logic):

    '''  '''

    @SessionEngine.configure('cookies')
    class CookieSessions(SessionEngine):

      '''  '''

      def load(self, context):

        '''  '''

        pass

      def commit(self, context, session):

        '''  '''

        pass


  __all__ = (
    'Cookies',
  )
