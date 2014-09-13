# -*- coding: utf-8 -*-

"""

  HTTP redirect logic
  ~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# runtime
from canteen.base import logic
from canteen.core import runtime

# canteen utils
from canteen.util import decorators

# core session API
from ..session import SessionEngine


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):


  @decorators.bind('http.redirects')
  class Redirects(logic.Logic):  # pragma: no cover

    """  """

    @SessionEngine.configure('redirects')
    class RedirectSessions(SessionEngine):

      """  """

      def load(self, context):

        """  """

        raise NotImplementedError('Method `RedirectSessions.load` is not'
                                  ' yet implemented.')

      def commit(self, context, session):

        """  """

        raise NotImplementedError('Method `RedirectSessions.commit` is not'
                                  ' yet implemented.')
