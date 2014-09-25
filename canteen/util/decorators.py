# -*- coding: utf-8 -*-

"""

  decorator utils
  ~~~~~~~~~~~~~~~

  useful (and sometimes critical) decorators, for use inside and
  outside :py:mod:`canteen`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

from __future__ import print_function


# noinspection PyPep8Naming
class classproperty(property):

  """ Custom decorator for class-level property getters.
      Usable like ``@property`` and chainable with
      ``@memoize``, as long as ``@memoize`` is used as
      the inner decorator. """

  # noinspection PyMethodOverriding
  def __get__(self, instance, owner):

    """ Return the property value at the class level.

        :param instance: Current encapsulating object
        dispatching via the descriptor protocol,
        ``None`` if we are being dispatched from the
        class level.

        :param owner: Corresponding owner type, available
        whether we're dispatching at the class or instance
        level.

        :returns: Result of a ``classmethod``-wrapped,
        ``property``-decorated method. """

    return classmethod(self.fget).__get__(None, owner)()


def singleton(target):

  """ Mark a ``target`` class as a singleton, for use with the dependency
      injection system. Classes so-marked will be factoried on first-access and
      subsequently returned for all matching dependency requests.

      :param target: Target class to treat as a singleton.

      :raises RuntimeError: If something other than a class is marked for
        singleton mode.

      :returns: Decorated ``target`` class, after it has been marked. """

  if isinstance(target, type):
    setattr(target, '__singleton__', True)  # indicate this is a singleton class
    return target
  raise RuntimeError('Only classes may be marked/decorated'
                     ' as singletons. Got: "%s".' % target)  # pragma: no cover


# noinspection PyPep8Naming
class bind(object):

  """ Encapsulated binding config for an injectable meta-implementor of
      ``meta.Proxy.Component``. Allows specification of simple string names to
      be matched during dependency injection. """

  __alias__ = None  # injection alias (i.e. `source.<alias> == <target>`)
  __target__ = None  # target for injection - i.e. what should be injected
  __config__ = None  # optional *args and **kwargs to wrap ``config`` (above)
  __namespace__ = True  # do we namespace this property under it's superbind?

  def __init__(self, alias=None, namespace=True, *args, **kwargs):

    """ Initialize this binding.

        :param alias: String alias for the target object to be bound. Defaults
          to ``None``, in which case the target function or class' ``__name__``
          will be used.

        :param namespace: ``bool`` flag to activate namespacing. Used on methods
          to explicitly bind them, but namespace them under the class binding
          they are mounted from.

        :param *args:  """

    self.__alias__, self.__config__, self.__namespace__ = (
      alias,
      (args, kwargs) if (args or kwargs) else None,
      namespace)  # wrap `decorators.config` (optional)

  def __repr__(self):  # pragma: no cover

    """ Generate a pleasant string representation for this binding.

        :returns: String representation for this binding, in the format
          ``<binding 'name'>``. """

    return "<binding '%s'>" % self.__alias__ or self.__target__.__name__

  # noinspection PyUnresolvedReferences
  def __call__(self, target):

    """ Dispatch this binding (the second half of a closured decorator flow) by
        scanning the target for subbindings (if applicable) and preparing (and
        subsequently attaching) an object to describe configuration.

        :param target: Target object (usually a ``function`` or ``class``) to
          *decorate* by scanning for sub-bindings and attaching a object
          describing any injectable resources.

        :raises TypeError: If a ``target`` is passed that is not a valid
          meta-implementor of ``Proxy.Registry`` or ``Proxy.Component``.

        :returns: Decorated ``target``, after scanning for bindings and
          attaching any appropriate configuration objects. """

    from ..core import meta  # no deps in util. ever. :)

    # default to binding name
    self.__alias__ = self.__alias__ or target.__name__

    # install aliases
    target.__binding__, target.__target__, self.__target__ = (
      self, self.__alias__, target)

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
        target.__aliases__, target.__bindings__ = (
          _aliases, frozenset(_bindings) if _bindings else None)

        # bind locally, and internally
        return target  # args no longer supported @TODO(sgammon): look at this

      # only registry-enabled class trees can use ``bind``
      raise TypeError('Only meta-implementors of `meta.Proxy.Registry`'
                      ' (anything meta-deriving from `Registry` or `Component`'
                      ' can be bound to injection names.')  # pragma: no cover

    # allow wrapping of hook responders
    from ..core import hooks
    if self.__config__ and self.__config__[1] and (
      isinstance(self.__config__[1]['wrap'], hooks.HookResponder)):
      self.__config__[1]['wrap'].__binding__ = self

    # are we decorating a method?
    return self.__config__[1]['wrap'](target) if (
      self.__config__ and 'wrap' in self.__config__[1]) else target
