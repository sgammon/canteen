# -*- coding: utf-8 -*-

'''

  canteen: content API
  ~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# core runtime
from .. import runtime


class ContentFilter(object):

  '''  '''

  __func__ = None
  __wrap__ = None
  __hooks__ = None
  __registered__ = False

  def __init__(self, **hooks):

    '''  '''

    # pull out inner wrap, if any
    if 'wrap' in hooks:
      self.__wrap__ = hooks['wrap']
      del hooks['wrap']

    self.__hooks__ = frozenset(hooks.keys())

  def __register__(self, context):

    '''  '''

    self.__registered__ = True
    for i in self.__hooks__:
      runtime.Runtime.add_hook(i, (context, self.__func__))

  def __call__(self, func):

    '''  '''

    self.__func__ = self.__wrap__(func) if self.__wrap__ else func
    return self
