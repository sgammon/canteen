# -*- coding: utf-8 -*-

'''

  apptools util: decorators

  this package provides useful decorators that crosscut the regular
  functional bounds of apptools' main packages. stuff in here is
  generally used everywhere.

  :author: Sam Gammon <sam@momentum.io>
  :copyright: (c) momentum labs, 2013
  :license: The inspection, use, distribution, modification or implementation
            of this source code is governed by a private license - all rights
            are reserved by the Authors (collectively, "momentum labs, ltd")
            and held under relevant California and US Federal Copyright laws.
            For full details, see ``LICENSE.md`` at the root of this project.
            Continued inspection of this source code demands agreement with
            the included license and explicitly means acceptance to these terms.

'''


# stdlib
import inspect


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
