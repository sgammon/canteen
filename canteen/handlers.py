# -*- coding: utf-8 -*-

'''

  canteen handlers
  ~~~~~~~~~~~~~~~~

  classes for building handler classes that respond to incoming
  requests over HTTP, websockets, or similar transport layers.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# meta
from .core import injection


class Handler(object):

  '''  '''

  __metaclass__ = injection.Compound

  def __init__(self):

    '''  '''

    import pdb; pdb.set_trace()


class WebHandler(Handler):

  '''  '''

  def wuddup(self):

    '''  '''

    return self.sayhello('hi')
