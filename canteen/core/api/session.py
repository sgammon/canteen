# -*- coding: utf-8 -*-

'''

  canteen: core session API
  ~~~~~~~~~~~~~~~~~~~~~~~~~

  exposes an API for creating and maintaining session state for
  both cyclical and realtime connection models.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''


# stdlib
import abc

# core & model APIs
from . import cache
from . import CoreAPI
from canteen import model

# canteen utils
from canteen.util import decorators


class Session(object):

  '''  '''

  __data__ = None

  class __metaclass__(type):

    '''  '''

    def __new__(cls, name, bases, property_map):

      '''  '''

      return super(cls, cls).__new__(cls, name, bases, property_map)

  ## == Get/Set == ##
  def set(self, key, value, exception=False):

    '''  '''

    pass

  def get(self, key, default=None, exception=False):

    '''  '''

    pass

  # attribute protocol
  __getattr__ = lambda self, key: self.get(key, exception=AttributeError)
  __setattr__ = lambda self, key, value: self.set(key, value, exception=AttributeError)

  # item protocol
  __getitem__ = lambda self, key: self.get(key, exception=KeyError)
  __setitem__ = lambda self, key, value: self.set(key, value, exception=KeyError)

  ## == Save/Load == ##
  def save(self):

    '''  '''

    pass

  @classmethod
  def load(self):

    '''  '''

    pass


@decorators.bind('sessions')
class SessionAPI(CoreAPI):

  '''  '''

  pass


__all__ = (
  'Session',
  'SessionAPI'
)
