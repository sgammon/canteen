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
import ast as pyast

# utils
from canteen.util import ast


## Globals
_seen_keepers = set()
_keeper_artifacts = set()


class ArtifactMatcher(ast.MatchVisitor):

  '''  '''

  # terms and node types to match against
  node_types = (pyast.Import, pyast.ImportFrom)
  term = frozenset(('canteen', 'canteen.Page', 'Page', 'canteen.Service', 'Service', 'canteen.Logic', 'Logic'))

  def match(self, identifier):

    '''  '''

    if any((term == identifier) for term in self.term):
      print '!!! MATCH: `%s` in `%s` !!!' % (identifier, self.name)
      return True
    return False


@ast.chain(matcher=ArtifactMatcher)
class ArtifactTracker(ast.SpliceTransformer):

  '''  '''

  kept_modules = []

  def __init__(self, loader, name, module):

    '''  '''

    self.name, self.module, self.loader, self.keep = name, module, loader, False
    self.kept_modules.append((self.name, self.module))

  def visit_Import(self, node):

    '''  '''

    print '   seen: import %s' % ', '.join((n.name for n in node.names))
    return node

  def visit_ImportFrom(self, node):

    '''  '''

    print '   seen: from %s import %s' % (node.module or '', ', '.join((n.name for n in node.names)))
    return node
