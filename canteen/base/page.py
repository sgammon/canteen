# -*- coding: utf-8 -*-

'''

  canteen: page base
  ~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# DI & util
from . import handler


class Page(handler.Handler):

  '''  '''

  __owner__ = "Page"


__all__ = ('Page',)
