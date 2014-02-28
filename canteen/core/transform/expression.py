# -*- coding: utf-8 -*-

'''

  canteen block transforms
  ~~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import copy
import itertools

# sibling transforms
from .block import BlockTransformer


class ExpressionMacro(object):

  '''  '''

  def __init__(self, args, expr):

    '''  '''

    self.args, self.expr, self.has_body = args, expr, False

  def expand(self, node, call_args, body=None):

    '''  '''

    assert not body
    if len(call_args) != len(self.args):
      raise TypeError('Invalid number of arguments for expression macro.')
    return BlockTransformer(dict(itertools.izip(self.args, call_args))).visit(copy.deepcopy(self.expr))
