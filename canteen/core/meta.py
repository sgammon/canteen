# -*- coding: utf-8 -*-

"""

  core meta
  ~~~~~~~~~

  metaclass tools and APIs.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# utils
from ..util import struct, decorators


## Globals
_owner_map = {}
grab = lambda x: x.__func__ if hasattr(x, '__func__') else x
owner = lambda x: intern(x.__owner__ if hasattr(x, '__owner__') else x.__name__)
construct = lambda cls, n, b, p: type.__new__(cls, n, b, p)
metachain = lambda cls, n, b, p: (
  cls.__metachain__.append(construct(cls, n, b, p)) or cls.__metachain__[-1])
is_component = lambda x: issubclass(x.__class__, Proxy.Component)


class MetaFactory(type):

  """ Meta class factory, used to prepare core metaclasses for use as
      functionality sentinels that compound functionality all the way up the
      tree as they are defined.

      This class is meta-abstract, meaning it must be used as a parent or
      metaclass to a more concrete implementation and cannot be instantiated or
      used directly. """

  __owner__, __metachain__, __root__ = "BaseMeta", [], True

  def __new__(mcs, name=None, bases=None, properties=None):

    """ Construct a new ``MetaFactory`` concrete class, implementing the
        ``initialize`` protocol for bootstrapping meta-implementing classes
        dynamically, potentially with DI-enabled MRO.

        :param name: String name for a new metaimplementor of ``MetaFactory``.

        :param bases: Tuple of base classes in the calling definition.

        :param properties: ``dict`` map of ``key => value`` class-level
          attributes.

        :raises NotImplementedError: If direct construction is attempted (i.e.
          not via Python's metaclass internals or a manual call of the same
          signautre), as ``MetaFactory`` is abstract.

        :returns: Factoried ``MetaFactory`` meta-implementor. """

    if not name or not bases or not (
      isinstance(properties, dict)):  # pragma: no cover
      raise NotImplementedError('`MetaFactory` is meta-abstract'
                                ' and cannot be constructed directly.')

    # get ready to construct, do so immediately for ``MetaFactory`` itself
    if '__root__' in properties and properties['__root__']:
      del properties['__root__']  # treat as a root - init directly and continue
      return construct(mcs, name, bases, properties)

    # patch class name to owner if it's embedded
    name = name if (
        (name != '__metaclass__' or '__owner__' not in properties)) else (
          properties['__owner__'])

    # construct, yo. then unconditionally apply it to the meta chain and return
    # also, defer to the class' ``initialize``, or any of its bases if they have
    # ``initialize`, for constructing the actual class.
    return ((grab(properties['initialize'] if 'initialize' in properties else
                  getattr((x for x in bases if hasattr(x, 'initialize')).next(),
                          'initialize')))(*(mcs, name, bases, properties))) if (
                            'initialize' in properties or any((
                              hasattr(b, 'initialize') for b in bases))
                                ) else metachain(mcs, name, bases, properties)

  def mro(cls):

    """ Assemble MRO (Method Resolution Order) to enable proper class composure
        patterns for ``MetaFactory``.

        :returns: All available mixin classes are mixed into the target MRO to
          enable a fully composure-based inheritance system. """

    # override metaclass MRO to make them superimpose-able on each other
    if not cls.__metachain__:
      return type.mro(cls)

    # make sure to enforce MRO semantics
    seen, tree, order = set(), [], type.mro(cls)
    for group in ([order[0]], order[1:-2], cls.__metachain__, order[-2:]):
      for base in group:
        if base not in seen: seen.add(base), tree.append(base)
    return tuple(tree)

  __repr__ = lambda cls: "<meta '%s.%s'>" % (cls.__owner__, cls.__name__)


class Base(type):

  """ Acts as a concrete anchor to core metaclasses. Can be used in an
      ``isinstance`` check to identify classes used in the meta-construction and
      initialization of downstream types and objects. """

  __owner__, __metaclass__, __root__ = "Base", MetaFactory, True


class Proxy(object):

  """ Container class for core metaclasses. Used to package references to
      structures that radically change Python's class system, such that one must
      explicitly use a ``Proxy.something`` qualified path as a metaclass. """


  class Factory(Base):

    """ Metaclass that enforces a pattern whereby concrete classes are passed
        through a factory function for construction. """

    __hooks__ = []

    def initialize(cls, name, bases, properties):

      """ Construct a new ``Factory`` concrete class. Dispatched when
          ``Factory`` or further-downstream core structures are used as
          metaclasses.

          :param name: Name of the target class to factory.
          :param bases: Tuple of target class bases.
          :param properties: Map of class-level attributes.

          :returns: Prepared ``Factory`` initializor class. """

      def metanew(_cls, _name, _bases, _properties):

        """ Closure that overrides ``__new__`` to inject custom class
            construction behavior.

            :param _cls: Target class to inject custom construction behavior on.

            :param _name: Name of the downstream class to factory with custom
              construction behavior.

            :param _bases: Tuple of bases for the downstream class to factory
              with custom construction behavior.

            :param _properties: Map of class-level attributes for downstream
              class desiring custom construction behavior.

            :returns: Properly constructed (and potentially, registered via
              ``Proxy.Registry``) downstream target class. """

        # if this metaclass implements the ``Proxy.Register`` class,
        #  defer to _cls.register directly after construction
        if issubclass(_cls, Proxy.Registry):
          return grab(_cls.register)(_cls, construct(*(
            _cls, _name, _bases, _properties)))
        return construct(_cls, _name, _bases, _properties)  # pragma: nocover

      # drop down if we already have a metachain for this tree
      if cls.__metachain__: properties['__new__'] = metanew

      # construct, yo. then unconditionally apply it to the metachain and return
      return metachain(cls, name, bases, properties)


  class Registry(Factory):

    """ Metaclass that enforces a pattern whereby classes are registered in a
        central datastructure according to their ``__bases__`` directly before
        or after class construction. """

    __chain__ = {}

    def iter_children(cls):

      """ Iterate over a parent class' registered child classes, one at a time.

          :returns: Yields child classes, one at a time. """

      for obj in cls.__chain__[owner(cls)]:
        if obj is cls: continue  # skip the parent class
        yield obj

    def children(cls):

      """ Retrieve a list of all this parent class' registered children.

          :returns: ``list`` of this ``cls``'s children. """

      # remember to filter-out weakrefs that have died
      return [child for child in cls.iter_children()]

    @staticmethod
    def register(meta, target):

      """ Register a new constructed subclass at ``target``, utilizing
          ``meta``'s chain.

          :param meta: Base ``chain`` that should be used for to register
            the ``target`` meta subclass.

          :param target: Target meta subclass to add to ``meta``'s metachain
            and register.

          :returns: ``target`` that was registered. """

      _owner = owner(target)

      # check to see if bases are only roots, if it is a root
      # create a new metabucket
      if not any((
        (False if x in (object, type) else True) for x in target.__bases__)):
        meta.__chain__[_owner] = []
        return target

      # resolve owner and construct
      for base in target.__bases__:
        if not base in (object, type):
          if _owner not in meta.__chain__: meta.__chain__[_owner] = []
          meta.__chain__[_owner].append(target)
      return target


  class Component(Registry):

    """ Decorate a class tree as capable of being injected as DI ``components``,
        which are bound to simple string names and made available
        application-wide at ``self``. """

    __target__ = None
    __binding__ = None
    __injector_cache__ = {}
    __map__ = {}  # holds map of all platform instances

    @decorators.classproperty
    def singleton_map(cls):

      """ Retrieve the application-wide map of singleton classes, bound to their
          names.

          :returns: Map of known singletons for the current execution flow. """

      return cls.__map__

    @classmethod
    def reset_cache(mcs):

      """ Reset injector caches. """

      mcs.__injector_cache__ = {}
      mcs.__class__.__injector_cache__ = {}

    @classmethod
    def prepare(mcs, target):

      """ Prepare ``target`` (usually ``cls``) for injection, possibly resolving
          a global singleton object to be returned upon matching attribute
          requests.

          :param target: Target class to prepare for later injection.

          :returns: Bound ``target``, after mapping any bound ``__binding__``
            aliases, methods, etc. """

      if (not hasattr(target, '__binding__')) or target.__binding__ is None:
        return  # non-bound classes don't need preparation

      alias = (  # resolve name, instantiate and register instance singleton
        target.__binding__.__alias__ if (
          hasattr(target.__binding__, '__alias__') and (
            isinstance(target.__binding__, basestring))) else target.__name__)

      if hasattr(target, '__singleton__') and target.__singleton__:
        # if we already have a singleton, give that
        if alias in mcs.__map__: return mcs.__map__[alias]

        # otherwise, startup a new singleton
        mcs.__map__[alias] = target()
        return mcs.__map__[alias]
      return target  # pragma: nocover

    @staticmethod
    def inject(cls):

      """ Parse/consider bindings attached to the target ``cls``, providing the
          final concrete class and set of injectable items.

          :returns: Two-item tuple of 1) the final concrete class (after
            ``prepare`` is invoked) and a manifest of inejctable bindings,
              passed as a Python ``set``. """

      # allow class to "prepare" itself (potentially instantiating a singleton)
      concrete = (cls.__class__.prepare(cls) if (
        hasattr(cls.__class__, 'prepare')) else cls)

      # allow class to indicate it does not wish to inject
      if concrete is None: return

      # gather injectable attributes
      _injectable = set()
      if hasattr(cls, '__bindings__'):
        for iterator in (cls.__dict__.iteritems(),
                         cls.__class__.__dict__.iteritems()):
          for prop, value in iterator:
            if cls.__bindings__:
              if prop in cls.__bindings__:
                func = (
                  cls.__dict__[prop] if not isinstance(cls.__dict__[prop], (
                    staticmethod, classmethod))
                  else cls.__dict__[prop].__func__)
                do_namespace = func.__binding__.__namespace__ if (
                  cls.__binding__.__namespace__) else False
                _injectable.add((
                  prop, func.__binding__.__alias__ or prop, do_namespace))

      # return bound injectables or the whole set
      return concrete, _injectable or (
        set(filter(lambda x: not x.startswith('__'),
            concrete.__dict__.iterkeys())))

    @staticmethod
    def collapse(cls, spec=None):

      """ Collapse available ``component`` items into a mapping of names to
          objects which can respond to attribute requests for those paths.

          :param spec: Base class to use as *perspective* for the DI collapse
            and response. Currently unused, but could easily be used to produce
            an aspect- or interface- based (stricter) DI system, rather than the
            wild-west-resolve-through-a-dictionary default in canteen.

          :returns: Collapsed DI pool, ready to be used for resolving dependency
            requests with registered attribute values at deeply-specified
            paths. """

      # try the injector cache
      if (cls, spec) not in Proxy.Component.__injector_cache__:

        # otherwise, collapse and build one
        property_bucket = {}
        for metabucket in Proxy.Registry.__chain__.iterkeys():
          for concrete in filter(is_component,
                                  Proxy.Component.__chain__[metabucket]):

            namespace = ''
            responder, properties = concrete.inject(concrete) or (None, {})

            # filter out classes that opt-out of injection
            if not responder: continue

            if hasattr(concrete, '__binding__'):

              # @TODO(sgammon): what the fuck does this shit even do
              def do_pluck(klass, obj, pool):

                """ First-level closure that prepares a ``pluck`` function to
                    properly grab an ``obj`` from the DI ``pool``, in the
                    context of ``klass``.

                    :param klass: Class context for which we would like to
                      prepare our ``pluck`` function. Exposes the base type to
                      the inner closure and keeps it around.

                    :param obj: Object singleton that can be used as a base for
                      resolving dependencies mapped to this class.

                    :param pool: Reference upwards to the main DI resource pool.

                    :returns: Prepared and closured ``pluck`` function, which is
                      particularly useful in a structure like a
                      :py:class:`struct.CallbackProxy`."""

                def pluck(property_name):

                  """ Second-level closure that plucks a property (at
                      ``property_name``) from the DI pool encapsulated in the
                      outer closure, in the context of ``klass``.

                      :param property_name: Property name that we would like to
                        resolve from ``klass`` or ``obj``, bound from the outer
                        closure function.

                      :raises AttributeError: If the requested ``property_name``
                        could not be resolved, by virtue of the fact that this
                        function makes use of ``getattr`` directly.

                      :returns: The value at the given ``property_name``, if
                        any, or raises ``AttributeError``, per standard Python
                        attribute resolution protocol. """

                  # dereference property aliases
                  if hasattr(klass, '__aliases__') and (
                    property_name in klass.__aliases__):
                    return getattr(obj, klass.__aliases__[property_name])
                  if hasattr(obj, property_name):
                    return getattr(obj, property_name)  # pragma: nocover

                  if klass.__binding__ and klass.__binding__.__alias__:
                    parent_ref = '.'.join((
                      klass.__binding__.__alias__, property_name))
                    if parent_ref in pool:
                      return pool[parent_ref]

                return setattr(pluck, 'target', klass) or pluck

              if concrete.__binding__:
                property_bucket[concrete.__binding__.__alias__] = (
                  struct.CallbackProxy(do_pluck(*(
                    concrete,
                    responder,
                    property_bucket
                  ))))

                if concrete.__binding__.__namespace__:
                  namespace = concrete.__binding__.__alias__

            for bundle in properties:

              # clear vars
              prop, alias, _global = None, None, False

              if not isinstance(bundle, tuple):  # pragma: no cover
                _key = '.'.join((namespace, bundle)) if namespace else bundle
                property_bucket[_key] = (responder, bundle)
                continue

              prop, alias, _global = bundle
              _key = alias
              if _global:
                _key = '.'.join((namespace, alias)) if namespace else alias
                property_bucket[_key] = (responder, prop)
                continue
              property_bucket[_key] = (responder, prop)

        if not property_bucket: return {}  # if it's empty, don't cache

        # set in cache, unless empty
        Proxy.Component.__injector_cache__[(cls, spec)] = property_bucket

      # return from cache
      return Proxy.Component.__injector_cache__[(cls, spec)]
