# -*- coding: utf-8 -*-

'''

  canteen: decorator utils
  ~~~~~~~~~~~~~~~~~~~~~~~~

  useful (and sometimes critical) decorators, for use inside and
  outside :py:mod:`canteen`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

from __future__ import print_function

# stdlib
import datetime


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


def singleton(target):

  '''  '''

  if isinstance(target, type):
    setattr(target, '__singleton__', True)  # indicate this is a singleton class
    return target
  raise RuntimeError('Only classes may be marked/decorated as singletons. Got: "%s".' % target)


## `` ``
class bind(object):

  '''  '''

  __alias__ = None  # injection alias (i.e. `source.<alias> == <target>`)
  __target__ = None  # target for injection - i.e. what should be injected
  __config__ = None  # optional *args and **kwargs to wrap ``config`` (above)
  __namespace__ = True  # do we namespace this property under it's superbind? (methods only)

  def __init__(self, alias=None, namespace=True, *args, **kwargs):

    '''  '''

    self.__alias__, self.__config__, self.__namespace__ = (
      alias,
      (args, kwargs) if (args or kwargs) else None,
      namespace  # wrap `decorators.config` (optional)
    )

  def __repr__(self):

    '''  '''

    return "<binding '%s'>" % self.__alias__ or self.__target__.__name__

  def __call__(self, target):

    '''  '''

    from ..core import meta  # no deps in util. ever. :)

    # default to binding name
    self.__alias__ = self.__alias__ or target.__name__

    # install aliases
    target.__binding__, target.__target__, self.__target__ = self, self.__alias__, target

    # are we decorating a class?
    if isinstance(target, type):

      if issubclass(target.__class__, meta.Proxy.Registry):

        _bindings, _aliases, _hooks = set(), {}, []

        # prepare singleton if requested
        if hasattr(target, '__singleton__') and target.__singleton__:
          target.__class__.prepare(target)

        # scan for "bound" methods (bound for DI, not for Python)
        for mapping in (target.__dict__, target.__class__.__dict__):

          for k, v in mapping.iteritems():

            if k.startswith('__'): continue

            # is this a wrapped method? unwrap it
            if isinstance(v, (staticmethod, classmethod)):
              v = v.__func__  # unwrap from wrapped class/static decorator

            # is this a bound (i.e. dependency-injected) method?
            if hasattr(v, '__binding__') and v.__binding__:
              _bindings.add(k)
              if v.__binding__.__alias__:
                _aliases[v.__binding__.__alias__] = k

            # is this a hook method? register with self
            if hasattr(v, '__hooks__') and v.__hooks__:
              v.__register__(target)

        # attach bindings to target class
        target.__aliases__, target.__bindings__ = _aliases, frozenset(_bindings) if _bindings else None

        # bind locally, and internally
        return config(target, *self.__config__[0], **self.__config__[1]) if self.__config__ else target

      # only registry-enabled class trees can use ``bind``
      raise TypeError('Only meta-implementors of `meta.Proxy.Registry`'
                      ' (anything meta-deriving from `Registry` or `Component`'
                      ' can be bound to injection names.')

    # allow wrapping of hook responders
    from ..core import hooks
    if self.__config__ and self.__config__[1] and isinstance(self.__config__[1]['wrap'], hooks.HookResponder):
      self.__config__[1]['wrap'].__binding__ = self

    # are we decorating a method?
    return self.__config__[1]['wrap'](target) if (self.__config__ and 'wrap' in self.__config__[1]) else target


__all__ = (
  'classproperty',
  'bind',
  'singleton'
)
