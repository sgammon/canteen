# -*- coding: utf-8 -*-

"""

  uwsgi runtime
  ~~~~~~~~~~~~~

  integrates :py:mod:`canteen` with :py:mod:`uwsgi`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# core
from ..core import runtime

# util
from ..util import debug
from ..util import decorators

# logic
from ..logic.realtime import TERMINATE


try:  # pragma: no cover

  with runtime.Library('uwsgi', strict=True) as (library, uwsgi):

    # logger
    logging = debug.Logger('uWSGI')


    @decorators.bind('uwsgi')
    class uWSGI(runtime.Runtime):

      """ WIP """

      def callback(self, start_response):

        """  """

        def responder(status, headers):

          """  """

          try:
            return start_response(status, headers)
          except IOError:
            return

        return responder

      def handshake(self, key, origin=None):

        """ WIP """

        uwsgi.websocket_handshake(key, origin)

      def send(self, payload, binary=False):

        """ WIP """

        return (uwsgi.websocket_send if not binary else (
              uwsgi.websocket_send_binary))(payload)

      def receive(self, blocking=True):

        """ WIP """

        try:
          return uwsgi.websocket_recv_nb if not blocking else (
                    uwsgi.websocket_recv)()

        except IOError:
          return TERMINATE

      def close(self):

        """ WIP """


    uWSGI.set_precedence(True)  # we're running *inside* uWSGI guys

except ImportError: pass
