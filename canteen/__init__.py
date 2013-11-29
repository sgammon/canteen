# -*- coding: utf-8 -*-

'''

  canteen
  ~~~~~~~

  a minimal web framework for the modern web

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# canteen :)
from .rpc import *
from .core import *
from .util import *
from .test import *
from .model import *
from .runtime import *
from .__main__ import *
from .dispatch import *
from .exceptions import *

# specific exports
from .core.meta import Proxy
from .core.runtime import Library
from .core.runtime import Runtime
from .core.platform import Platform

walk()  # kick off deep-import
