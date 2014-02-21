# -*- coding: utf-8 -*-

'''

  canteen transform core
  ~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import copy
import ast as pyast

# canteen internals
from . import runtime
from ..util import ast


## Globals
_BODY_TERM = '__body__'
_TRANSFORM_DECORATOR = ast.transformer


class BlockVisitor(ast.BlockScanner):

  '''  '''

  term = _BODY_TERM


class BlockTransformer(ast.MatchTransformer):

  '''  '''

  term = _BODY_TERM


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
    return BlockTransformer(dict(izip(self.args, call_args))).visit(copy.deepcopy(self.expr))


class BlockMacro(object):

  '''  '''

  def __init__(self, args, statements):

    '''  '''

    self.args, self.statements = args, statements
    visitor = BlockVisitor()
    visitor.visit(ast.Module(statements))
    self.matched_body = visitor.found

  def expand(self, node, call_args, body=None):

    '''  '''

    if len(call_args) != len(self.args):
      raise TypeError('Invalid number of arguments for block macro.')
    return BlockTransformer(dict(izip(self.args, call_args)), body).visit(self.rewrite_locations(pyast.If(pyast.Num(1), copy.deepcopy(self.statements), []), node))


@ast.chain
class BlockExpander(ast.SpliceTransformer):

  '''  '''

  def __init__(self, module, definitions=None):

    '''  '''

    self.module, self.definitions = module, (definitions or {})

  def parse(self, code):

    '''  '''

    code = pyast.parse(code)  # make an AST first

    for node in code.body:
      if not isinstance(node, pyast.FunctionDef):
        continue
      if not item.decorator_list:
        continue  # it's not decorated, so it definitely doesn't have an AST transform decorator

      for decorator_block in item.decorator_list:

        # @TODO(sgammon): match against attributed names too
        if any(
          (isinstance(decorator_block, pyast.Name) and decorator_block.id == _TRANSFORM_DECORATOR.__name__)  # it matches as a decorator name
          ):

          # extract name and args
          name, args = node.name, [arg.id for arg in node.args.args]

          # enforce signature requirements
          if node.args.vararg or node.args.kwarg or node.args.defaults:
            raise TypeError('Macro %s has unsupported signature.' % name)

          if len(node.body) == 1 and isinstance(item.body[0], pyast.Expr):
            yield name, ExpressionMacro(args, item.body[0].value)

          else:
            yield name, BlockMacro(args, item.body)

  def consider(self, module, names, mapping):

    '''  '''

    try:
      mod = __import__(module, mapping, None, ['*'])
    except Exception as err:
      raise ImportError('Failed to locate or import AST-enabled module: `%s`. Error: %s' % (module, err))

    # trim `c` or `o` off compiled bytecode files
    filename = mod.__file__
    if filename.lower().endswith(('c', 'o')):
      filename = filename[:-1]

    # open source and read
    with open(filename, 'U') as handle:
      code = handle.read()

    # collect found macros
    blocks, desired = {}, frozenset(names)
    for name, block in self.parse(code):

      if name in desired or '*' in desired:
        blocks[name] = block

      self.definitions[name] = block  # map to appropriate local def
    return blocks

  def visit_Expr(self, node):

    '''  '''

    if isinstance(node.value, pyast.Call) and isinstance(node.value.func, pyast.Name) and node.value.func.id in self.definitions:
      result = self._handle_expr_call(node.value, (ExpressionMacro, BlockMacro))
      if isinstance(result, pyast.expr):
        result = self.rewrite_locations(pyast.Expr(result), node)
      return result
    return node

  def visit_With(self, node):

    '''  '''

    if isinstance(node.context_expr, pyast.Call) and isinstance(node.context_expr.func, pyast.Name) and node.context_expr.func.id in self.definitions:
      if not isinstance(self.definitions[node.context_expr.func.id], BlockMacro):
        raise TypeError('Cannot use expression macro in `with` block.')
      if not self.definitions[node.context_expr.func.id].matched_body:
        raise RuntimeError('Target block macro has no body substitution.')
      return self.definitions[node.context_expr.func.id].expand(node, node.context_expr.args, map(self.visit, node.body))
    else:
      new = pyast.With(node.context_expr, node.optional_vars, map(self.visit, node.body))
      new.lineno, new.col_offset = node.lineno, node.col_offset
      return new

  def visit_Call(self, node):

    '''  '''

    if isinstance(node.func, pyast.Name) and node.func.id in self.definitions:
      return self._handle_expr_call(node, ExpressionMacro)
    return node

  # @TODO(sgammon): add support for regular Imports

  def visit_ImportFrom(self, node):

    '''  '''

    if node.module and node.module.endswith('.__macros__'):
      module_name = node.module[:-11]
      names = dict((alias.name, alias.asname or alias.name) for alias in node.names)
      self.definitions.update(self.consider(module_name, names, self.module and self.module.__dict__))
      return None
    return node

  def _handle_expr_call(self, node, macrotype):

    '''  '''

    if node.keywords or node.starargs or node.kwargs:
      raise TypeError('Cannot call macro with kwargs or star args.')
    if not isinstance(self.definitions[node.func.id], macrotype):
      raise TypeError('Cannot handle expression call for macro of invalid type `%s`.' % self.definitions[node.func.id].__class__.__name__)
    if self.definitions[node.func.id].matched_body:
      raise TypeError('Cannot handle call macro with body substitution.')
    return self.definitions[node.func.id].expand(node, map(self.visit, node.args))


__all__ = (
  'BlockVisitor',
  'BlockTransformer',
  'ExpressionMacro',
  'BlockMacro'
)
