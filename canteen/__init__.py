# -*- coding: utf-8 -*-

'''

  canteen
  ~~~~~~~

  a minimal web framework for the modern web

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

debug, __version__ = __debug__, (1, 0)


# canteen :)
from .rpc import *
from .core import *
from .util import *
from .test import *
from .base import *
from .logic import *
from .model import *
from .runtime import *
from .dispatch import *
from .exceptions import *


__all__ = globals()  # export all the things
