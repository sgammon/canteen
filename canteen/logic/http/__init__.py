# -*- coding: utf-8 -*-

'''

  canteen: HTTP logic
  ~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# symbols
from .etags import ETags
from .agent import UserAgent
from .caching import Caching
from .cookies import Cookies
from .redirects import Redirects
from .semantics import HTTPSemantics, url


# exports
__all__ = (
  'url',
  'ETags',
  'Cookies',
  'Caching',
  'Redirects',
  'UserAgent',
  'HTTPSemantics'
)
