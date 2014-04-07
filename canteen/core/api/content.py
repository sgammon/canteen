# -*- coding: utf-8 -*-

'''

  canteen: content API
  ~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core runtime
from .. import runtime


class ContentFilter(object):

  '''  '''

  __func__, __hooks__ = None, None

  def __init__(self, **hooks):

    '''  '''

    self.__hooks__ = frozenset(hooks.keys())

  def __register__(self, context):

    '''  '''

    for i in self.__hooks__:
      runtime.Runtime.add_hook(i, (context, self.__func__))

  def __call__(self, func):

    '''  '''

    self.__func__ = func
    return self
