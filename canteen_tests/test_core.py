# -*- coding: utf-8 -*-

'''

  canteen core tests
  ~~~~~~~~~~~~~~~~~~

  tests canteen's core, which contains abstract/meta code for constructing
  and gluing together the rest of canteen.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''


class CoreMetaTest(test.FrameworkTest):

  ''' Tests for :py:mod:`canteen.core.meta`. '''

  def test_module_proxy(self):

    ''' Test the metaproxy that exposes `Factory`, `Registry`
        and `Component`. '''

    assert hasattr(meta, 'Proxy')
    assert hasattr(meta, 'MetaFactory')

  def test_proxy_attributes(self):

    ''' Test that `meta.Proxy` properly exposes attributes
        for each meta-metaclass. '''

    assert hasattr(Proxy, 'Factory')
    assert hasattr(Proxy, 'Registry')
    assert hasattr(Proxy, 'Component')


class MetaFactoryTest(test.FrameworkTest):

  ''' Tests for :py:class:`canteen.core.meta.MetaFactory`. '''

  def test_new_concrete_metafactory(self):

    ''' Test that :py:class:`canteen.core.meta.MetaFactory`
        cannot be constructed directly. '''

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory()

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory('hi')

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory('hi', (object,))

  def test_new_meta_metafactory(self):

    ''' Test that :py:class:`canteen.core.meta.MetaFactory`
        is usable as a metaclass, via `Proxy.Factory`. '''

    assert isinstance(meta.Proxy.Factory('TargetMeta', (object,), {}), type)

  def test_meta_mro(self):

    ''' Test that `meta.Proxy.Factory` properly overwrites
        object MRO. '''

    klass = meta.Proxy.Factory('TargetMeta', (object,), {'__metaclass__': meta.Proxy.Factory})
    assert klass.__mro__ == (klass, object)


class ClassFactoryTest(test.FrameworkTest):

  ''' Tests for `meta.Proxy.Factory`. '''

  def test_construct_factory(self):

    ''' Try constructing a new `meta.Proxy.Factory`
        meta-implementor. '''

    # make fake factory sub
    class FactoryMetaclass(object):
      __metaclass__ = meta.Proxy.Factory

    assert hasattr(FactoryMetaclass, 'initialize')
    assert not hasattr(FactoryMetaclass, 'inject')
    assert not hasattr(FactoryMetaclass, 'register')

  def test_initialize_factory(self):

    ''' Try overriding `meta.Proxy.Factory.initialize`
        in a meta-implementor. '''

    # make subfactory
    class FactorySubclass(meta.Proxy.Factory):
      def initialize(cls, name, bases, properties):
        klass = type.__new__(cls, name, bases, properties)
        klass.__initialized__ = True
        return klass

    # make implementor
    class CoolImplementor(object):
      __metaclass__ = FactorySubclass

    assert hasattr(FactorySubclass, 'initialize')
    assert hasattr(CoolImplementor, '__initialized__')
    assert CoolImplementor.__initialized__ == True


class ClassRegistryTest(test.FrameworkTest):

  ''' Tests for `meta.Proxy.Registry`. '''

  def test_construct_registry(self):

    ''' Try constructing a new `meta.Proxy.Registry`
        meta-implementor. '''

    # make fake registry sub
    class RegistryMetaclass(object):
      __metaclass__ = meta.Proxy.Registry

    assert hasattr(RegistryMetaclass, 'register')
    assert hasattr(RegistryMetaclass, 'initialize')
    assert not hasattr(RegistryMetaclass, 'inject')

  def test_registry_internals(self):

    ''' Make sure internals of `meta.Proxy.Registry`
        work correctly. '''

    # make a registered class tree
    class RegistryTestRegistry(object):
      __owner__, __metaclass__ = "RegistryTestRegistry", meta.Proxy.Registry

    # make implementors
    class RegisteredOne(RegistryTestRegistry): pass
    class RegisteredTwo(RegistryTestRegistry): pass

    # test chain internals
    assert "RegistryTestRegistry" in RegistryTestRegistry.__metaclass__.__chain__
    assert RegisteredOne in [i for i in RegistryTestRegistry.__metaclass__.__chain__["RegistryTestRegistry"]]
    assert RegisteredTwo in [i for i in RegistryTestRegistry.__metaclass__.__chain__["RegistryTestRegistry"]]

  def test_iterate_children(self):

    ''' Try iterating over a registered class'
        children. '''

    # make a registered class tree
    class IterateChildrenRegistry(object):
      __owner__, __metaclass__ = "IterateChildrenRegistry", meta.Proxy.Registry

    # make implementors
    class IterationChildOne(IterateChildrenRegistry): pass
    class IterationChildTwo(IterateChildrenRegistry): pass
    class IterationChildThree(IterateChildrenRegistry): pass

    _results = []
    for child in IterateChildrenRegistry.iter_children():
      _results.append(child)

    assert len(_results) == 3
    for i in (IterationChildOne, IterationChildTwo, IterationChildThree):
      assert i in _results

  def test_list_children(self):

    ''' Try retrieving a list of a registered class'
        children. '''

    # make a registered class tree
    class ListChildrenRegistry(object):
      __owner__, __metaclass__ = "ListChildrenRegistry", meta.Proxy.Registry

    # make implementors
    class ListChildOne(ListChildrenRegistry): pass
    class ListChildTwo(ListChildrenRegistry): pass
    class ListChildThree(ListChildrenRegistry): pass

    _results = ListChildrenRegistry.children()
    assert len(_results) == 3
    for i in (ListChildOne, ListChildTwo, ListChildThree):
      assert i in _results


class ClassComponentTest(test.FrameworkTest):

  ''' Tests for :py:class:`meta.Proxy.Component`. '''

  def test_construct_component(self):

    ''' Try constructing a new `meta.Proxy.Component`
        meta-implementor. '''

    # make fake component sub
    class ComponentMetaclass(object):
      __metaclass__ = meta.Proxy.Component

    assert hasattr(ComponentMetaclass, 'inject')
    assert hasattr(ComponentMetaclass, 'register')
    assert hasattr(ComponentMetaclass, 'initialize')
