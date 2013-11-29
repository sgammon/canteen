# -*- coding: utf-8 -*-

'''

  canteen decorators
  ~~~~~~~~~~~~~~~~~~

  useful (and sometimes critical) decorators, for use inside and
  outside :py:mod:`canteen`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''


## ``classproperty`` - use like ``@property``, but at the class-level.
class classproperty(property):

  ''' Custom decorator for class-level property getters.
      Usable like ``@property`` and chainable with
      ``@memoize``, as long as ``@memoize`` is used as
      the inner decorator. '''

  def __get__(self, instance, owner):

    ''' Return the property value at the class level.

        :param instance: Current encapsulating object
        dispatching via the descriptor protocol,
        ``None`` if we are being dispatched from the
        class level.

        :param owner: Corresponding owner type, available
        whether we're dispatching at the class or instance
        level.

        :returns: Result of a ``classmethod``-wrapped,
        ``property``-decorated method. '''

    return classmethod(self.fget).__get__(None, owner)()


## ``memoize`` - cache the output of a property descriptor call
class memoize(property):

  ''' Custom decorator for property memoization. Usable
      like ``@property`` and chainable with ``@classproperty``,
      the utility decorator above. '''

  _value = None
  __initialized__ = False

  def __get__(self, instance, owner):

    ''' If we have a cached value attached to this
        context, return it.

        :param instance: Current encapsulating object
        dispatching via the descriptor protocol, or
        ``None`` if we are being dispatched from the
        class level.

        :param owner: Owner type for encapsulating
        object, if dispatched at the instance level.

        :raises: Re-raises all exceptions encountered
        in the case of an unexpected state during
        delegated property dispatch.

        :returns: Cached value, if any. If there is
        no cached value, defers to decorated method. '''

    if not self.__initialized__:
      if isinstance(self.fget, classproperty):
        self._value = classmethod(self.fget.fget).__get__(None, owner)()
      else:
        self._value = self.fget.__get__(instance, owner)()
      self.__initialized__ = True
    return self._value


## `` ``
class cached(object):

  '''  '''

  __func__ = None
  __cache__ = {}

  def __init__(self, callable):

    '''  '''

    self.__func__ = callable

  def wrap(self, instance):

    '''  '''

    def cache(*args, **kwargs):
      ps, kw = tuple(args), tuple(kwargs.items())
      if (ps, kw) not in self.__cache__:
        self.__cache__[(ps, kw)] = self.__func__(instance, *args, **kwargs)
      return self.__cache__[(ps, kw)]

    return cache

  def __get__(self, instance, owner):

    '''  '''

    return self.wrap(instance)


## `` ``
class bind(object):

  '''  '''

  __alias__ = None
  __target__ = None

  def __init__(self, alias):

    '''  '''

    assert isinstance(alias, basestring)
    self.__alias__ = alias

  def __call__(self, target):

    '''  '''

    from ..core import meta  # _no deps in util. ever. :)_

    if not issubclass(target.__class__, meta.Proxy.Registry):
      raise TypeError('Only meta-implementors of `meta.Proxy.Registry`'
                      ' (anything meta-deriving from `Registry` or `Component`'
                      ' can be bound to injection names.')

    # bind locally, and internally
    target.__target__, self.__target__ = self.__alias__, target
    return target
