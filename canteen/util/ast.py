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
import pdb
import copy
import importlib


## Globals
__chain__ = {}
ast = importlib.import_module('ast')


def chain(matcher=None):

  '''  '''

  global __chain__

  def ast_chain(callable):

    '''  '''

    __chain__[callable.__name__] = (matcher, callable)
    return callable

  return ast_chain


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

  node_types = None
  __metaclass__ = abc.ABCMeta

  def __init__(self, loader, name, module):

    '''  '''

    self.name, self.module, self.loader, self.found = name, module, loader, False

  def generic_visit(self, node):

    '''  '''

    if self.filter(node):
      for identifier in self.extract(node):
        if self.match(identifier):
          self.found = True

    return super(MatchVisitor, self).generic_visit(node)

  def generic_extract(self, node):

    '''  '''

    raise RuntimeError("I don't know how to generically extract :(")

  def extract(self, node):

    '''  '''

    # route to AST-node-specific methods for this node
    for id in self.extractor_map.get(type(node), self.extractor_map[None])(self, node):
      yield id

    #pdb.set_trace()

    # collapse (extract) the tree for each branch under this node
    #for branch in (getattr(node, i) for i in node._fields):
    #  if not isinstance(branch, (set, tuple, list, frozenset)):
    #    # extract stringy/constant values
    #    yield branch
    #  else:
    #    # otherwise, recurse to follow the tree
    #    for sub_branch in branch:
    #      for id in self.extract(sub_branch):
    #        yield id

  def extract_import(self, node):

    '''  '''

    # regular imports only have names
    if isinstance(node, ast.Import):
      for n in node.names: yield n.name

    # for `from`-style imports, extract main module *and* names
    if isinstance(node, ast.ImportFrom):
      if node.module: yield node.module
      for n in node.names: yield n.name

  def extract_call(self, node):

    '''  '''

    #pdb.set_trace()
    raise StopIteration()

  def extract_name(self, node):

    '''  '''

    #pdb.set_trace()
    raise StopIteration()

  def extract_with(self, node):

    '''  '''

    #pdb.set_trace()
    raise StopIteration()

  def extract_class(self, node):

    '''  '''

    #pdb.set_trace()


    yield node.name  # class name
    for entry in node.decorator_list:
      yield self.extract(entry)  # re-extract decorators
    raise StopIteration()

  def extract_func(self, node):

    '''  '''

    #pdb.set_trace()
    raise StopIteration()

  def extract_attribute(self, node):

    '''  '''

    #pdb.set_trace()
    raise StopIteration()

  def filter(self, node):

    '''  '''

    # by default: check against class-level installed node types
    return (self.node_types and isinstance(node, self.node_types)) or (not self.node_types)

  ## build map of extractor tools
  extractor_map = {

    ast.Call: extract_call,
    ast.Name: extract_name,
    ast.Import: extract_import,
    ast.ImportFrom: extract_import,
    ast.Attribute: extract_attribute,
    ast.FunctionDef: extract_func,
    ast.ClassDef: extract_class,
    ast.With: extract_with,
    None: generic_visit

  }

  def __call__(self, tree):

    '''  '''

    self.visit(tree)  # proxy callable syntax to `visit`
    return self.found  # indicate found status

  @abc.abstractmethod
  def match(self, identifier):

    '''  '''

    raise NotImplementedError('`%s.match` is abstract.' % self.__class__.__name__)


class TermMatcher(MatchVisitor):

  '''  '''

  term = None  # term to scan for

  def match(self, identifier):

    '''  '''

    return ((identifier in self.term) if isinstance(self.term, (frozenset, set, list, tuple)) else identifier == self.term)


class BlockScanner(TermMatcher):

  '''  '''

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

  def __call__(self, tree):

    '''  '''

    return self.visit(tree)  # proxy callable syntax to `visit`


class MatchTransformer(SpliceTransformer):

  '''  '''

  def visit_Name(self, node):

    '''  '''

    if node.id in self.args:
      if not isinstance(node.ctx, ast.Load):
        new_node = copy.deepcopy(self.args[node.id])
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
