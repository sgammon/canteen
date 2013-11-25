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


class MetaFactory(type):

  '''  '''

  __owner__, __metachain__, __chain__ = "BaseMeta", [], {}

  def __new__(cls, name, bases, properties):

    '''  '''

    # get ready to construct, do so immediately for ``MetaFactory`` itself
    if name is "MetaFactory": return type.__new__(cls, name, bases, properties)

    def metanew(_cls, _name, _bases, _properties):

      '''  '''

      klass = type.__new__(_cls, _name, _bases, _properties)

      # check to see if bases are only roots, if it is a root create a new metabucket
      if not any(((False if x in (object, type) else True) for x in _bases)):
        cls.__chain__[intern(klass.__owner__ if hasattr(klass, '__owner__') else klass.__name__)] = []
        return klass

      # resolve owner and construct
      for base in _bases:
        if base in (object, type):
          continue

        owner = intern(base.__owner__ if hasattr(base, '__owner__') else base.__name__)
        if owner not in cls.__chain__: cls.__chain__[owner] = []

        # there can only be one owner
        cls.__chain__[owner].append(klass)

      return klass

    # drop down if we already have a metachain for this tree
    if cls.__metachain__: properties['__new__'] = metanew

    # construct, yo. then unconditionally apply it to the metachain and return
    klass = type.__new__(cls, name, bases, properties)
    return cls.__metachain__.append(klass) or klass

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

  def __repr__(cls):

    '''  '''

    return "<meta '%s.%s'>" % (cls.__owner__, cls.__name__)


class Base(type):

  '''  '''

  __owner__ = "Base"
  __metaclass__ = MetaFactory


class Proxy(object):

  '''  '''


  class Factory(Base):

    '''  '''

    def initialize(cls):

      '''  '''

      pass


  class Registry(Factory):

    '''  '''

    def register(cls):

      '''  '''

      pass


  class Component(Registry):

    '''  '''

    def inject(cls, requestor):

      '''  '''

      pass
