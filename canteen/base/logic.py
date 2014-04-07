# -*- coding: utf-8 -*-

'''

  canteen: logic base
  ~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core API
from ..core import meta
from ..util import decorators


@decorators.singleton
class Logic(object):

  '''  '''

  __owner__ = "Logic"
  __metaclass__ = meta.Proxy.Component


__all__ = ('Logic',)
