# -*- coding: utf-8 -*-

'''

  canteen: core meta
  ~~~~~~~~~~~~~~~~~~

  metaclass tools and APIs.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''


## Globals
_owner_map = {}
grab = lambda x: x.__func__ if hasattr(x, '__func__') else x
owner = lambda x: intern(x.__owner__ if hasattr(x, '__owner__') else x.__name__)


class MetaFactory(type):

  '''  '''

  __owner__, __metachain__, __root__ = "BaseMeta", [], True

  def __new__(cls, name, bases, properties):

    '''  '''

    # get ready to construct, do so immediately for ``MetaFactory`` itself and other explicit roots
    if '__root__' in properties and properties['__root__']:
      del properties['__root__']  # treat as a root - init directly and continue
      return type.__new__(cls, name, bases, properties)

    # construct, yo. then unconditionally apply it to the metachain and return also, defer to the class'
    #  ``initialize``, or any of its bases if they have ``initialize`, for constructing the actual class.
    return ((grab(properties['initialize'] if 'initialize' in properties else
              getattr(filter(lambda x: hasattr(x, 'initialize'), bases)[0], 'initialize')))(*(
                cls, name, bases, properties))) if (
                  'initialize' in properties or any((hasattr(b, 'initialize') for b in bases))
                ) else (cls.__metachain__.append(type.__new__(cls, name, bases, properties)) or cls.__metachain__[-1])

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

    @classmethod
    def add_hook(cls, hook):

      '''  '''

      return cls.__hooks__.append(hook) or cls

    @staticmethod
    def initialize(cls, name, bases, properties):

      '''  '''

      def metanew(_cls, _name, _bases, _properties):

        '''  '''

        # if this metaclass implements the ``Proxy.Register`` class,
        #  defer to _cls.register directly after construction
        if issubclass(_cls, Proxy.Registry):
          return grab(_cls.register)(_cls, type.__new__(_cls, _name, _bases, _properties))
        return type.__new__(_cls, _name, _bases, _properties)

      # drop down if we already have a metachain for this tree
      if cls.__metachain__: properties['__new__'] = metanew

      # construct, yo. then unconditionally apply it to the metachain and return
      return cls.__metachain__.append(type.__new__(cls, name, bases, properties)) or cls.__metachain__[-1]


  class Registry(Factory):

    '''  '''

    __chain__ = {}

    def iter_children(cls):

      '''  '''

      for child in cls.__chain__[owner(cls)]:
        if child is cls: continue
        yield child

    def children(cls):

      '''  '''

      return [child for child in cls.iter_children()]

    @staticmethod
    def register(meta, target):

      '''  '''

      # check to see if bases are only roots, if it is a root create a new metabucket
      if not any(((False if x in (object, type) else True) for x in target.__bases__)):
        meta.__chain__[owner(target)] = []
        return target

      # resolve owner and construct
      for base in target.__bases__:
        if base in (object, type):
          continue

        if owner(target) not in meta.__chain__: meta.__chain__[owner(target)] = []
        meta.__chain__[owner(target)].append(target)
      return target


  class Component(Registry):

    '''  '''

    @staticmethod
    def inject(cls, requestor):

      '''  '''

      pass
