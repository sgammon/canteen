# -*- coding: utf-8 -*-

"""

  stdlib runtime
  ~~~~~~~~~~~~~~

  runs :py:mod:`canteen`-based apps on python's stdlib library,
  :py:mod:`wsgiref`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# core
from ..core import runtime


with runtime.Library('wsgiref') as (library, wsgiref):

  # stdlib
  simple_server = library.load('simple_server')


  class StandardWSGI(runtime.Runtime):

    """  """

    __default__ = True

    def bind(self, interface, port):  # pragma: no cover

      """  """

      return simple_server.make_server(interface, port, self.dispatch)
