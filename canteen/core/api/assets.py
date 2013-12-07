# -*- coding: utf-8 -*-

'''

  canteen: core assets API
  ~~~~~~~~~~~~~~~~~~~~~~~~

  exposes a core API for easily accessing and managing static
  assets attached to a :py:mod:`canteen`-based product.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# core API & util
from . import CoreAPI
from canteen.util import decorators


@decorators.bind('assets')
class AssetsAPI(CoreAPI):

  '''  '''

  __config__ = None  # asset configuration, if any

  @property
  def config(self):

    '''  '''

  def style_url(self):

    '''  '''

    pass

  def script_url(self):

    '''  '''

    pass

  def image_url(self):

    '''  '''

    pass
