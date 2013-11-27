# -*- coding: utf-8 -*-

'''

  canteen core tests
  ~~~~~~~~~~~~~~~~~~

  tests canteen's core, which contains abstract/meta code for constructing
  and gluing together the rest of canteen.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# testing
from canteen import test

# core meta
from canteen.core import meta
from canteen.core.meta import Proxy
from canteen.core.meta import MetaFactory


class CoreMetaTest(test.FrameworkTest):

  '''  '''

  def test_module_proxy(self):

    '''  '''

    assert hasattr(meta, 'Proxy')
    assert hasattr(meta, 'MetaFactory')

  def test_proxy_attributes(self):

    '''  '''

    assert hasattr(Proxy, 'Factory')
    assert hasattr(Proxy, 'Registry')
    assert hasattr(Proxy, 'Component')


class MetaFactoryTest(test.FrameworkTest):

  '''  '''

  def test_new_concrete_metafactory(self):

    '''  '''

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory()

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory('hi')

    with self.assertRaises(NotImplementedError):
      meta.MetaFactory('hi', (object,))

  def test_new_meta_metafactory(self):

    '''  '''

    assert isinstance(meta.Proxy.Factory('TargetMeta', (object,), {}), type)

  def test_meta_mro(self):

    '''  '''

    klass = meta.Proxy.Factory('TargetMeta', (object,), {'__metaclass__': meta.Proxy.Factory})
    assert klass.__mro__ == (klass, object)


class ClassFactoryTest(test.FrameworkTest):

  '''  '''

  pass


class ClassRegistryTest(test.FrameworkTest):

  '''  '''

  pass


class ClassComponentTest(test.FrameworkTest):

  '''  '''

  pass
