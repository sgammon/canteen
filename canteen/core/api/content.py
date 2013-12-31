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

  __func__, __hooks__ = None, None

  def __init__(self, **hooks):

    '''  '''

    self.__hooks__ = []
    for k in hooks:
      if hooks[k]: self.__hooks__.append(k)

  def __call__(self, func):

    '''  '''

    for hook in self.__hooks__:
      runtime.Runtime.add_hook(hook, func)
    return func
