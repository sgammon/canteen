# -*- coding: utf-8 -*-

'''

  canteen page base
  ~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# base handler
from . import handler


class Page(handler.Handler):

  '''  '''

  def wuddup(self):

    '''  '''

    return self.sayhello('hi')
