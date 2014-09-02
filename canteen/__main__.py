# -*- coding: utf-8 -*-

"""

  runscript
  ~~~~~~~~~

  accepts calls to ``canteen`` as a module. can be run with
  ``python -m canteen`` or ``python -m canteen/``, the latter
  assuming you have it installed right next to you.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# utils
from .util import walk
from .dispatch import (run, app)

walk(), run()
