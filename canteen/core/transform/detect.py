# -*- coding: utf-8 -*-

'''

  canteen detection core
  ~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import pdb  # @TODO(sgammon): remove this
import itertools
import ast as pyast

# utils
from canteen.util import ast


## Globals
_seen_keepers = set()
_keeper_artifacts = set()


class ArtifactMatcher(ast.TermMatcher):

  '''  '''

  # terms and node types to match against
  node_types = (pyast.Import, pyast.ImportFrom)
  term = 'canteen'


@ast.chain(matcher=ArtifactMatcher)
class ArtifactTracker(ast.SpliceTransformer):

  '''  '''

  kept_modules = []
  canteen_modules = []

  def __init__(self, loader, name, module):

    '''  '''

    self.name, self.module, self.loader, self.keep = name, module, loader, False
    (self.kept_modules if not name.startswith('canteen.') else self.canteen_modules).append((self.name, self.module))
