# -*- coding: utf-8 -*-

'''

  canteen: injection core
  ~~~~~~~~~~~~~~~~~~~~~~~

  tools for dependency injection - essentially, walking the
  structure exposed by classes in :py:mod:`core.meta` to
  combine dependencies into compound classes.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# canteen meta
from .meta import Proxy


class Delegate(object):

  ''' '''

  __bridge__ = None  # holds bridge for current class to collapsed component set
  __target__ = None  # holds injection target for this delegate (that we will answer for)

  class __metaclass__(type):

    '''  '''

    def __new__(cls, name_or_target, bases=None, properties=None):

      '''  '''

      # if it only comes through with a target, it's a subdelegate
      if bases or properties:
        # it's `Delegate` probably - construct it as normal
        name, target = name_or_target, None
        return type.__new__(cls, name, bases, properties)

      # otherwise, construct with an MRO attribute injection
      name, target = None, name_or_target

      def injection_responder(klass, key):

        '''  '''

        # @TODO(sgammon): make things not jank here (for instance, don't `collapse` every time)
        try:
          bridge = Proxy.Component.collapse(klass)
          if isinstance(bridge[key], tuple):
            return getattr(*bridge[key])  # bridge key is tuple of (responder, attribute)
          return bridge[key]  # return value directly if it's not a tuple
        except KeyError:  # pragma: nocover
          raise AttributeError('Could not resolve attribute \'%s\''
                               ' on item \'%s\'.' % (key, klass))

      # inject properties onto MRO delegate, then construct
      return type.__new__(cls.__class__, 'Delegate', (object,), {
        '__bridge__': None,
        '__getattr__': classmethod(injection_responder),
        '__metaclass__': cls,
        '__repr__': cls.__repr__,
        '__target__': target
      })

    def __repr__(cls):  # pragma: nocover

      '''  '''

      return "<delegate root>" if not cls.__target__ else "<delegate '%s'>" % cls.__target__.__name__

  @classmethod
  def bind(cls, target):

    '''  '''

    # wrap in Delegate class context as well
    return cls.__metaclass__.__new__(cls, target)


class Compound(type):

  '''  '''

  __seen__ = set()
  __delegate__ = None

  def mro(cls):

    '''  '''

    for base in cls.__bases__:
      # check if we've seen any of these bases
      if base not in (object, type) and base in cls.__class__.__seen__:
        break
    else:
      # never seen this before - roll in our delegate
      origin = type.mro(cls)
      delegate = Delegate.bind(cls)
      cls.__class__.__seen__.add(cls)

      return (
        [origin[0]] +
        [i for i in filter(lambda x: x not in (object, type), origin[1:])] +
        [y for y in filter(lambda z: z in (object, type), origin[1:])] +
        [delegate]
      )

    return type.mro(cls)


class Bridge(object):

  '''  '''

  __metaclass__ = Compound


__all__ = (
  'Delegate',
  'Compound',
  'Bridge'
)
