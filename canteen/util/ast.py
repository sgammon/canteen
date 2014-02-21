# -*- coding: utf-8 -*-

'''

  canteen AST tools
  ~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import abc
import ast
import deepcopy


## Globals
__chain__ = []
__transformers__ = {}


def chain(callable):

  '''  '''

  global __chain__
  __chain__.append(callable)
  return callable


def transformer(callable):

  '''  '''

  global __transformers__
  __transformers__[callable.__name__] = callable
  return callable


class ContextChanger(ast.NodeVisitor):

  '''  '''

  def __init__(self, context):

    '''  '''

    self.context = context

  def visit_Name(self, node):

    '''  '''

    node.ctx = self.context
    self.generic_visit(node)

  visit_Attribute = visit_Subscript = visit_List = visit_Tuple = visit_Name


class MatchVisitor(ast.NodeVisitor):

  '''  '''

  __metaclass__ = abc.ABCMeta

  def __init__(self):

    '''  '''

    self.found = False

  @abc.abstractmethod
  def match(self, node):

    '''  '''

    raise NotImplementedError('`ScanVisitor.match` is abstract.')


class BlockScanner(MatchVisitor):

  '''  '''

  term = None  # term to scan for

  def match(self, node):

    '''  '''

    if isinstance(self.term, (frozenset, set, tuple)):
      return (node.value.id in self.term)
    return (node.value.id == self.term)


class SpliceTransformer(ast.NodeTransformer):

  '''  '''

  __metaclass__ = abc.ABCMeta

  def __init__(self, args, body=None):

    '''  '''

    self.args, self.body = args, body

  @staticmethod
  def rewrite_locations(node, old):

    '''  '''

    def _fix(node, line_no, col_offset):

      '''  '''

      # splice in line and column
      node.lineno, node.col_offset = line_no, col_offset
      map(lambda child: _fix(child, line_no, col_offset), ast.iter_child_nodes(node))
      return node

    return _fix(node, old.lineno, old.col_offset)  # kick off recursive rewrite


class MatchTransformer(SpliceTransformer):

  '''  '''

  def visit_Name(self, node):

    '''  '''

    if node.id in self.args:
      if not isinstance(node.ctx, ast.Load):
        new_node = deepcopy.deepcopy(self.args[node.id])
        ContextChanger(node.ctx).visit(new_node)
      else:
        new_node = self.args[node.id]
      return new_node
    return node

  def visit_Expr(self, node):

    '''  '''

    node = self.generic_visit(node)
    if self.body and isinstance(node.value, ast.Name) and self.match(node):
      return self.rewrite_locations(ast.If(ast.Num(1), self.body, []), node)

  @abc.abstractmethod
  def match(self, node):

    '''  '''

    raise NotImplementedError('`SpliceTransformer.match` is abstract.')


class ScanTransformer(MatchTransformer):

  '''  '''

  term = None  # term to scan for

  def match(self, node):

    '''  '''

    if isinstance(self.term, (frozenset, set, tuple)):
      return (node.value.id in self.term)
    return (node.value.id == self.term)


__all__ = (
  'ContextChanger',
  'ScanVisitor',
  'BlockScanner',
  'SpliceTransformer',
  'ScanTransformer'
)
