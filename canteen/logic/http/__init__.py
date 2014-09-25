# -*- coding: utf-8 -*-

"""

  HTTP logic
  ~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# symbols
from .agent import UserAgent
from .cookies import Cookies
from .semantics import HTTPSemantics, url


# exports
__all__ = ('url',
           'Cookies',
           'UserAgent',
           'HTTPSemantics')
