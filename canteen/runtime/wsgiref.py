# -*- coding: utf-8 -*-

'''

  canteen stdlib runtime
  ~~~~~~~~~~~~~~~~~~~~~~

  runs :py:mod:`canteen`-based apps on python's stdlib library,
  :py:mod:`wsgiref`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core
from ..core import runtime
from ..util import decorators


with runtime.Library('wsgiref') as (library, wsgiref):

  # stdlib
  simple_server = library.load('simple_server')


  class StandardWSGI(runtime.Runtime):

    '''  '''

    __default__ = True

    def bind(self, interface, port):

      '''  '''

      return simple_server.make_server(interface, port, self.dispatch)
