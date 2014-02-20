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

import ast


class Deferred(object):

  '''  '''

  def __init__(self):

    '''  '''

    pass

  def expand(self, node, args, body=None):

    '''  '''

    pass


class Deferrer(ast.NodeTransformer):

  '''  '''

  def __init__(self, module, symbols=None):

    '''  '''

    pass

  def visit_With(self, node):

    '''  '''

    pass

  def visit_Import(self, node):

    '''  '''

    pass

  def visit_ImportFrom(self, node):

    '''  '''

    pass

  def visit_Expr(self, node):

    '''  '''

    pass

  def visit_Call(self, node):

    '''  '''

    pass
