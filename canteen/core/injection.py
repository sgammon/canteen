# -*- coding: utf-8 -*-

"""

  core injection
  ~~~~~~~~~~~~~~

  tools for dependency injection - essentially, walking the
  structure exposed by classes in :py:mod:`core.meta` to
  combine dependencies into compound classes.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# canteen meta
from .meta import Proxy


class Delegate(object):

  """ Delegates property access for a given context to the system DI (dependency
      injection) pool. Items that mix a ``Delegate`` subclass into their MRO
      work transparently with injection. """

  __target__, __bridge__ = (
      None,  # holds injection target for this delegate
      None)  # holds bridge for current class to collapsed component set

  class __metaclass__(type):

    """ Metaclass to prepare new subclasses, wrapped as customized children of
        ``Delegate`` that contain their owner class for DI context. """

    def __new__(mcs, name_or_target, bases=None, properties=None):

      """ Construct a new ``Delegate`` subclass.

          :param name_or_target: Either the ``str`` name of a subtype extending
            ``Delegate`` directly or a name to wrap into an ephemeral
            ``Delegate`` type (mainly for use in labelling).

          :param bases: Unset (``None``) unless extending ``Delegate``,
            otherwise a tuple of ``bases``.

          :param properties: Unset (``None``) unless extending ``Delegate``,
            otherwise a ``dict`` mapping of class-level attributes and values.

          :returns: Factoried ``Delegate`` subtype, wrapped with an injection
            responder closure suitable for use in MRO-based dependency
            resolution. """

      # if it only comes through with a target, it's a subdelegate
      if bases or properties:

        # it's `Delegate` probably - construct it as normal
        name, target = name_or_target, None
        return type.__new__(mcs, name, bases, properties)

      # otherwise, construct with an MRO attribute injection
      name, target = None, name_or_target

      def injection_responder(klass, key):

        """ Injected responder for attribute accesses that hit the DI pool.
            Resolves a ``key`` for a given ``klass``, if possible.

            :param klass: Origin class for which we should generate a DI pool
              on-the-fly. This could be thought of as the *"perspective"* or
              *"client"* of a dependency *"request"*, due to be injected ASAP.

            :param key: Symbol that the caller would like to be provided by the
              DI pool, after exhausting more scope-specific options in the MRO
              chain.

            :raises AttributeError: If an attribute could not be found in the
              dependency pool, to simulate "not finding" a property on the
              origin ``klass``.

            :returns: Any result that the dependency pool can provide, from all
              known dependency resources available to ``klass``, available at
              ``key``. """

        # @TODO(sgammon): make things not jank here (don't always `collapse`)
        try:
          bridge = Proxy.Component.collapse(klass)
          if isinstance(bridge[key], tuple):  # pragma: no cover
            return getattr(*bridge[key])  # bridge key is (responder, attribute)
          return bridge[key]  # return value directly if it's not a tuple
        except KeyError:  # pragma: nocover
          raise AttributeError('Could not resolve attribute \'%s\''
                               ' on item \'%s\'.' % (key, klass))

      # inject properties onto MRO delegate, then construct
      return type.__new__(mcs.__class__, 'Delegate', (object,), {
        '__bridge__': None,
        '__getattr__': classmethod(injection_responder),
        '__metaclass__': mcs,
        '__repr__': mcs.__repr__,
        '__target__': target})

    def __repr__(cls):  # pragma: nocover

      """ Generate a string representation of the local ``Delegate``, including
          whatever class context we're running in, if any.

          :returns: String representation of a bound or root delegate. """

      return "<delegate root>" if not (
        cls.__target__) else "<delegate '%s'>" % cls.__target__.__name__

  @classmethod
  def bind(cls, target):

    """ Factory a new ``Delegate`` subclass, bound to the ``target`` context
        class.

        :param target: Subject class to bind and spawn a ``Delegate`` subtype
          for.

        :returns: Bound ``Delegate`` subtype, suitable for MRO mixing. """

    # wrap in Delegate class context as well
    return cls.__metaclass__.__new__(cls, target)


class Compound(type):

  """ Concrete class used as a metafactory for class structures that should
      enable attribute accesses for response from the DI pool.

      Use this class as a metaclass on items that should transparently work with
      attribute injection. """

  __seen__ = set()
  __delegate__ = None

  def mro(cls):

    """ Prepares MRO (Method Resolution Order) with a customized ``Delegate``
        that provides a view into the DI pool.

        :returns: Prepared MRO for a dependency-injected metatype, known as a
          ``Compound`` because it is essentially the product of itself and a
          collapsed set of ``Component`` injectables. """

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
        [delegate])

    return type.mro(cls)


class Bridge(object):

  """ Tiny utility class that can be used as a static ``Bridge`` into the DI
      pool. Suitable for use as an independent object, mounted wherever is
      convenient. """

  __metaclass__ = Compound
