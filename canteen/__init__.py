# -*- coding: utf-8 -*-

"""

  canteen
  ~~~~~~~

  a minimal web framework for the modern web

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

debug, __version__ = __debug__, (0, 0, 5)

# stdlib
import __builtin__

# canteen :)
from .core import *
from .base import *
from .logic import *

from .rpc import *
from .util import *
from .model import *
from .runtime import *
from .dispatch import *
from .exceptions import *


if debug: from .test import *

__all__ = [export for export in (locals().keys() + globals().keys()) if not (
    (export in __builtin__.__dict__ or export.startswith('__')))]
