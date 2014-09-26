# -*- coding: utf-8 -*-

"""

  core meta tests
  ~~~~~~~~~~~~~~~

  tests canteen's core, which contains abstract/meta code for constructing
  and gluing together the rest of canteen.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# testing
from canteen import test

# core meta
from canteen.core import meta
from canteen.core import injection
from canteen.core.meta import Proxy

# canteen util
from canteen.util import decorators


class CoreMetaTest(test.FrameworkTest):

  """ Tests for :py:mod:`canteen.core.meta` """

  def test_module_proxy(self):

    """ Test that metaproxy exposes `Factory`, `Registry` and `Component` """

    assert hasattr(meta, 'Proxy')
    assert hasattr(meta, 'MetaFactory')

  def test_proxy_attributes(self):

    """ Test that `meta.Proxy` properly exposes each meta-metaclass """

    assert hasattr(Proxy, 'Factory')
    assert hasattr(Proxy, 'Registry')
    assert hasattr(Proxy, 'Component')


class MetaFactoryTest(test.FrameworkTest):

  """ Tests for :py:class:`MetaFactory` """

  def test_new_concrete_metafactory(self):

    """ Test that `MetaFactory` cannot be constructed directly """

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory()

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory('hi')

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory('hi', (object,))

  def test_new_meta_metafactory(self):

    """ Test that `MetaFactory` is usable as a metaclass via `Proxy.Factory` """

    assert isinstance(meta.Proxy.Factory('TargetMeta', (object,), {}), type)

  def test_meta_mro(self):

    """ Test that `meta.Proxy.Factory` properly overwrites object MRO """

    klass = meta.Proxy.Factory('TargetMeta', (object,), {
        '__metaclass__': meta.Proxy.Factory})
    assert klass.__mro__ == (klass, object)


class ClassFactoryTest(test.FrameworkTest):

  """ Tests for `meta.Proxy.Factory` """

  def test_construct_factory(self):

    """ Test constructing a new `meta.Proxy.Factory` meta-implementor """

    # make fake factory sub
    class FactoryMetaclass(object):
      __metaclass__ = meta.Proxy.Factory

    assert hasattr(FactoryMetaclass, 'initialize')
    assert not hasattr(FactoryMetaclass, 'inject')
    assert not hasattr(FactoryMetaclass, 'register')

  def test_initialize_factory(self):

    """ Test overriding `meta.Proxy.Factory.initialize` in a metaimplementor """

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
    assert CoolImplementor.__initialized__ is True


class ClassRegistryTest(test.FrameworkTest):

  """ Tests for `meta.Proxy.Registry` """

  def test_construct_registry(self):

    """ Test constructing a new `meta.Proxy.Registry` metaimplementor """

    # make fake registry sub
    class RegistryMetaclass(object):
      __metaclass__ = meta.Proxy.Registry

    assert hasattr(RegistryMetaclass, 'register')
    assert hasattr(RegistryMetaclass, 'initialize')
    assert not hasattr(RegistryMetaclass, 'inject')

  def test_registry_internals(self):

    """ Test internals of `meta.Proxy.Registry` """

    # make a registered class tree
    class RegistryTestRegistry(object):
      __owner__, __metaclass__ = "RegistryTestRegistry", meta.Proxy.Registry

    # make implementors
    class RegisteredOne(RegistryTestRegistry): pass
    class RegisteredTwo(RegistryTestRegistry): pass

    # test chain internals
    registry = [i for i in (
        RegistryTestRegistry.__metaclass__.__chain__["RegistryTestRegistry"])]
    assert "RegistryTestRegistry" in (
        RegistryTestRegistry.__metaclass__.__chain__)
    assert RegisteredOne in registry
    assert RegisteredTwo in registry

  def test_iterate_children(self):

    """ Test iterating over a registered class' children """

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

    """ Test retrieving a list of a registered class children """

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

  """ Tests for :py:class:`meta.Proxy.Component` """

  def test_construct_component(self):

    """ Test constructing a new `meta.Proxy.Component` meta-implementor """

    # make fake component sub
    class ComponentMetaclass(object):
      __metaclass__ = meta.Proxy.Component

    assert hasattr(ComponentMetaclass, 'inject')
    assert hasattr(ComponentMetaclass, 'register')
    assert hasattr(ComponentMetaclass, 'initialize')

    return ComponentMetaclass

  def test_collapse(self):

    """ Test manually collapsing a class with known bindings """

    meta.Proxy.Component.reset_cache()


    @decorators.bind('injectable')
    class InjectableClass(self.test_construct_component()):

      """  """

      @decorators.bind('test', wrap=staticmethod)
      def test(self):

         """  """

      @decorators.bind('toplevel', wrap=staticmethod, namespace=False)
      def toplevel(self):

         """  """

    assert InjectableClass


    class TestCompound(object):
      __metaclass__ = injection.Compound


    class InjectedClass(TestCompound):

      """  """

      def test_blab(self):

        """  """

        assert self.toplevel
        assert self.injectable
        assert self.injectable.test

      def test_invalid(self):

        """  """

        self.invalid_property_here


    # manually perform a class collapse
    collapsed = meta.Proxy.Component.collapse(InjectedClass)

    # test collapse
    assert isinstance(collapsed, dict)
    assert 'injectable' in collapsed
    assert 'toplevel' in collapsed
    assert 'injectable.test' in collapsed

    # test full injection
    i = InjectedClass()
    assert i.test_blab
    i.test_blab()

    # make sure invalid attributes still fail
    with self.assertRaises(AttributeError):
      i.blabble

    with self.assertRaises(AttributeError):
      i.test_invalid()

    # clean up
    meta.Proxy.Component.reset_cache()

    return InjectedClass

  def test_singleton_map(self):

    """ Test setting a `Component` meta-implementor into `singleton` mode """


    @decorators.singleton
    @decorators.bind('singleton')
    class SingletonTest(self.test_construct_component()):

      """  """

      def get_self(self):

        """  """

        return self


    class TestCompound(object):

      """ Test compound object. """

      __metaclass__ = injection.Compound


    class CompoundSingletonTest(TestCompound):

      """  """

      def test_singleton(self):

        """  """

        assert self.singleton
        return self.singleton.get_self()

    # access the singleton to create one
    i = CompoundSingletonTest()
    singleton_one = i.test_singleton()
    singleton_two = i.test_singleton()

    # must be exactly equal
    assert singleton_one is singleton_two

    # check singleton's presence in the map
    assert singleton_one in SingletonTest.__class__.singleton_map.values()
    assert singleton_two in SingletonTest.__class__.singleton_map.values()
