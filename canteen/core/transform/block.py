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
import ast as pyast

# canteen internals
from canteen.util import ast


## Globals
_BODY_TERM = '__body__'
_TRANSFORM_DECORATOR = ast.chain


class BlockVisitor(ast.BlockScanner):

  '''  '''

  term = _BODY_TERM


class BlockTransformer(ast.MatchTransformer):

  '''  '''

  term = _BODY_TERM


class BlockMacro(object):

  '''  '''

  def __init__(self, args, statements):

    '''  '''

    self.args, self.statements = args, statements
    visitor = BlockVisitor()
    visitor.visit(pyast.Module(statements))
    self.matched_body = visitor.found

  def expand(self, node, call_args, body=None):

    '''  '''

    if len(call_args) != len(self.args):
      raise TypeError('Invalid number of arguments for block macro.')
    return BlockTransformer(dict(izip(self.args, call_args)), body).visit(self.rewrite_locations(pyast.If(pyast.Num(1), copy.deepcopy(self.statements), []), node))


#@ast.chain  # @TODO(sgammon): apply transforms someday
class BlockExpander(ast.SpliceTransformer):

  '''  '''

  def __init__(self, name, module, definitions=None):

    '''  '''

    self.name, self.seen, self.module, self.definitions = name, set(), module, (definitions or {})

  def parse(self, code):

    '''  '''

    code = pyast.parse(code)  # make an AST first

    for node in code.body:
      if not isinstance(node, (pyast.FunctionDef, pyast.ClassDef)) or not (hasattr(node, 'decorator_list') and node.decorator_list):
        continue  # it's not decorated, so it definitely doesn't have an AST transform decorator

      for decorator_block in node.decorator_list:

        # @TODO(sgammon): match against attributed names too
        if any((
          (isinstance(decorator_block, pyast.Name) and decorator_block.id == _TRANSFORM_DECORATOR.__name__),  # it matches as a decorator name
          (isinstance(decorator_block, pyast.Attribute) and ((decorator_block.value.id == 'ast') and (decorator_block.attr == 'transform')))  # matches `@ast.transform`
          )):

          # extract name and args
          if isinstance(node, pyast.FunctionDef):
            name, args = node.name, [arg.id for arg in node.args.args]

            # enforce signature requirements
            if node.args.vararg or node.args.kwarg or node.args.defaults:
              raise TypeError('Macro %s has unsupported signature.' % name)

          else:
            name, args = node.name, []

          if len(node.body) == 1 and isinstance(node.body[0], pyast.Expr):
            yield name, ExpressionMacro(args, node.body[0].value)

          else:
            yield name, BlockMacro(args, node.body)

  def match(self, node):

    '''  '''

    import pdb; pdb.set_trace()

  def consider(self, name, module, names, mapping):

    '''  '''

    # trim `c` or `o` off compiled bytecode files
    filename = module.__file__
    if filename.lower().endswith(('c', 'o')):
      filename = filename[:-1]

    # open source and read
    with open(filename, 'U') as handle:
      code = handle.read()

    # collect found macros
    blocks, desired = {}, frozenset(names or tuple())
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

    #print 'seen: `%s` in `%s`' % ('.'.join(filter(lambda x: x, (node.module or None, '.'.join((n.name for n in node.names))))), self.name)

    # @TODO(sgammon): add proper support for sniffing imports
    if node.module and all((
      ('ast' in node.module or any((n.name == 'ast') for n in node.names)),
      )):

      print ' !!!  found: `%s` in `%s`  !!! ' % ('.'.join((node.module or '', ', '.join((n.name for n in node.names)))), self.name)

      names = dict((alias.name, alias.asname or alias.name) for alias in node.names)
      if len(names) == 1 and 'ast' in names: names = None  # skip naming code if we only want AST tools (meta-detect)
      self.definitions.update(self.consider(self.name, self.module, names, self.module and self.module.__dict__))
      return node

    return node

  def visit_Import(self, node):

    '''  '''

    #print 'seen: `%s` in `%s`' % (', '.join((n.name for n in node.names)), self.name)

    #if self.match(node):
    #  print '!!! found match: %s !!!' % ','.join(node.names)
    for name in node.names:
      if 'ast' in name.name:
        print '!!! found match: `%s` in `%s`' % (name.name, self.name)

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