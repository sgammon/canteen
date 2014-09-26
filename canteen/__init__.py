# -*- coding: utf-8 -*-

"""

  canteen
  ~~~~~~~

  a minimal web framework for the modern web

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

debug, __version__ = __debug__, (0, 3)

# stdlib
import __builtin__; export = None

# yay modules!
from . import core
from . import rpc
from . import util
from . import test
from . import base
from . import model
from . import logic
from . import runtime
from . import dispatch
from . import exceptions

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


__all__ = [export for export in globals() if (
  export not in __builtin__.__dict__ and (
    not export.startswith('__')))]  # export all the things!
