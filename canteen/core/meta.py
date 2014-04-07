# -*- coding: utf-8 -*-

'''

  canteen: meta core
  ~~~~~~~~~~~~~~~~~~

  metaclass tools and APIs.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# utils
from ..util import struct, decorators


## Globals
_owner_map = {}
grab = lambda x: x.__func__ if hasattr(x, '__func__') else x
owner = lambda x: intern(x.__owner__ if hasattr(x, '__owner__') else x.__name__)
construct = lambda cls, name, bases, properties: type.__new__(cls, name, bases, properties)
metachain = lambda cls, n, b, p: cls.__metachain__.append(construct(cls, n, b, p)) or cls.__metachain__[-1]


class MetaFactory(type):

  '''  '''

  __owner__, __metachain__, __root__ = "BaseMeta", [], True

  def __new__(cls, name=None, bases=None, properties=None):

    '''  '''

    if not name or not bases or not isinstance(properties, dict):  # pragma: nocover
      raise NotImplementedError('`MetaFactory` is meta-abstract and cannot be constructed directly.')

    # get ready to construct, do so immediately for ``MetaFactory`` itself and other explicit roots
    if '__root__' in properties and properties['__root__']:
      del properties['__root__']  # treat as a root - init directly and continue
      return construct(cls, name, bases, properties)

    # construct, yo. then unconditionally apply it to the metachain and return also, defer to the class'
    #  ``initialize``, or any of its bases if they have ``initialize`, for constructing the actual class.
    return ((grab(properties['initialize'] if 'initialize' in properties else
              getattr((x for x in bases if hasattr(x, 'initialize')).next(), 'initialize')))(*(
                cls, name, bases, properties))) if (
                  'initialize' in properties or any((hasattr(b, 'initialize') for b in bases))
                ) else metachain(cls, name, bases, properties)

  def mro(cls):

    '''  '''

    # override metaclass MRO to make them superimposable on each other
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

  '''  '''

  __owner__, __metaclass__, __root__ = "Base", MetaFactory, True


class Proxy(object):

  '''  '''


  class Factory(Base):

    '''  '''

    __hooks__ = []

    def initialize(cls, name, bases, properties):

      '''  '''

      def metanew(_cls, _name, _bases, _properties):

        '''  '''

        # if this metaclass implements the ``Proxy.Register`` class,
        #  defer to _cls.register directly after construction
        if issubclass(_cls, Proxy.Registry):
          return grab(_cls.register)(_cls, construct(_cls, _name, _bases, _properties))
        return construct(_cls, _name, _bases, _properties)  # pragma: nocover

      # drop down if we already have a metachain for this tree
      if cls.__metachain__: properties['__new__'] = metanew

      # construct, yo. then unconditionally apply it to the metachain and return
      return metachain(cls, name, bases, properties)


  class Registry(Factory):

    '''  '''

    __chain__ = {}

    def iter_children(cls):

      '''  '''

      for obj in cls.__chain__[owner(cls)]:
        if obj is cls: continue  # skip the parent class
        yield obj

    def children(cls):

      '''  '''

      # remember to filter-out weakrefs that have died
      return [child for child in cls.iter_children()]

    @staticmethod
    def register(meta, target):

      '''  '''

      _owner = owner(target)

      # check to see if bases are only roots, if it is a root create a new metabucket
      if not any(((False if x in (object, type) else True) for x in target.__bases__)):
        meta.__chain__[_owner] = []
        return target

      # resolve owner and construct
      for base in target.__bases__:
        if not base in (object, type):
          if _owner not in meta.__chain__: meta.__chain__[_owner] = []
          meta.__chain__[_owner].append(target)
      return target


  class Component(Registry):

    '''  '''

    __target__ = None
    __binding__ = None
    __injector_cache__ = {}
    __map__ = {}  # holds map of all platform instances

    @decorators.classproperty
    def singleton_map(cls):

      '''  '''

      return cls.__map__

    @classmethod
    def reset_cache(cls):

      '''  '''

      cls.__injector_cache__ = {}
      cls.__class__.__injector_cache__ = {}
      return

    @staticmethod
    def collapse(cls, spec=None):

      '''  '''

      # try the injector cache
      if (cls, spec) not in Proxy.Component.__injector_cache__:

        # otherwise, collapse and build one
        property_bucket = {}
        for metabucket in Proxy.Registry.__chain__.iterkeys():
          for concrete in filter(lambda x: issubclass(x.__class__, Proxy.Component), Proxy.Component.__chain__[metabucket]):

            namespace = ''
            responder, properties = concrete.inject(concrete, cls.__target__, cls.__delegate__) or (None, {})
            if not responder: continue  # filter out classes that opt-out of injection

            if hasattr(concrete, '__binding__'):

              def do_pluck(klass, obj, pool):

                '''  '''

                def pluck(property_name):

                  '''  '''

                  # dereference property aliases
                  if hasattr(klass, '__aliases__') and property_name in klass.__aliases__:
                    return getattr(obj, klass.__aliases__[property_name])
                  if hasattr(obj, property_name):
                    return getattr(obj, property_name)  # pragma: nocover

                  if klass.__binding__ and klass.__binding__.__alias__:
                    parent_ref = '.'.join((klass.__binding__.__alias__, property_name))
                    if parent_ref in pool:
                      return pool[parent_ref]

                return setattr(pluck, 'target', klass) or pluck

              if concrete.__binding__:
                property_bucket[concrete.__binding__.__alias__] = struct.CallbackProxy(do_pluck(*(
                  concrete,
                  responder,
                  property_bucket
                )))

                if concrete.__binding__.__namespace__:
                  namespace = concrete.__binding__.__alias__

            for bundle in properties:

              # clear vars
              prop, alias, _global = None, None, False

              if not isinstance(bundle, tuple):
                property_bucket['.'.join((namespace, bundle)) if namespace else bundle] = (responder, bundle)
                continue

              prop, alias, _global = bundle
              if _global:
                property_bucket['.'.join((namespace, alias)) if namespace else alias] = (responder, prop)
                continue
              property_bucket[alias] = (responder, prop)

        # if it's empty, don't cache
        if not property_bucket: return {}

        # set in cache, unless empty
        Proxy.Component.__injector_cache__[(cls, spec)] = property_bucket

      # return from cache
      return Proxy.Component.__injector_cache__[(cls, spec)]

    @staticmethod
    def inject(cls, requestor, delegate):

      '''  '''

      # allow class to "prepare" itself (potentially instantiating a singleton)
      concrete = cls.__class__.prepare(cls) if hasattr(cls.__class__, 'prepare') else cls

      # allow class to indicate it does not wish to inject
      if concrete is None: return

      # gather injectable attributes
      _injectable = set()
      if hasattr(cls, '__bindings__'):
        for iterator in (cls.__dict__.iteritems(), cls.__class__.__dict__.iteritems()):
          for prop, value in iterator:
            if cls.__bindings__:
              if prop in cls.__bindings__:
                func = cls.__dict__[prop] if not isinstance(cls.__dict__[prop], (staticmethod, classmethod)) else cls.__dict__[prop].__func__
                do_namespace = func.__binding__.__namespace__ if cls.__binding__.__namespace__ else False
                _injectable.add((prop, func.__binding__.__alias__ or prop, do_namespace))

      # return bound injectables or the whole set
      return concrete, _injectable or set(filter(lambda x: not x.startswith('__'), concrete.__dict__.iterkeys()))

    @classmethod
    def prepare(cls, target):

      '''  '''

      if (not hasattr(target, '__binding__')) or target.__binding__ is None: return

      # resolve name, instantiate and register instance singleton
      alias = target.__binding__.__alias__ if (hasattr(target.__binding__, '__alias__') and isinstance(target.__binding__, basestring)) else target.__name__

      if hasattr(target, '__singleton__') and target.__singleton__:
        # if we already have a singleton, give that
        if alias in cls.__map__: return cls.__map__[alias]

        # otherwise, startup a new singleton
        cls.__map__[alias] = target()
        return cls.__map__[alias]
      return target  # pragma: nocover


__all__ = (
  'MetaFactory',
  'Base',
  'Proxy'
)
