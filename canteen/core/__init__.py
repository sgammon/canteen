# -*- coding: utf-8 -*-

"""

  core
  ~~~~

  classes, utilities and stuff that is core to the proper operation of canteen.
  meta stuff, abstract stuff, and runtime utilities.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# submodules
from .meta import *
from .hooks import *
from .runtime import *
from .injection import *


__all__ = ('meta',
           'hooks',
           'runtime',
           'injection')
