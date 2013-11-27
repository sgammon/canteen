# -*- coding: utf-8 -*-

'''

  canteen core meta tests
  ~~~~~~~~~~~~~~~~~~~~~~~

  tests the metaclass tools in canteen's core, which are responsible
  for metatools that generate factories/registries/components, etc.

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


class CoreMeta(test.FrameworkTest):

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
