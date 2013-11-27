# -*- coding: utf-8 -*-

'''

  canteen tests
  ~~~~~~~~~~~~~

  utilities for providing unittest functionality.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

if __debug__:


  # stdlib
  import sys
  import unittest

  # registry magic
  from .core import meta

  # just-in-case...
  try:
    import canteen_tests
    from canteen_tests import *
  except:
    pass


  class AppTest(unittest.TestCase):

    '''  '''

    __root__, __owner__, __metaclass__ = True, 'AppTest', meta.Proxy.Registry


  class FrameworkTest(unittest.TestCase):

    '''  '''

    __root__, __owner__, __metaclass__ = True, 'FrameworkTest', meta.Proxy.Registry


  def run(output=None, scope=(AppTest, FrameworkTest), format='text', verbosity=5, **kwargs):

    '''  '''

    # fill testsuite with found testcases
    master_suite, loader = [], unittest.TestLoader()

    for bucket in scope:
      suite = unittest.TestSuite()

      for child in bucket.iter_children():
        suite.addTests(loader.loadTestsFromTestCase(child))

      master_suite.append(suite)
    master_suite = unittest.TestSuite(master_suite)

    # allow for XML format
    if format == 'xml':
      if output is None:
        output = ".develop/tests"
      try:
        import xmlrunner
      except ImportError:
        raise RuntimeError('Cannot generate XML output without `xmlrunner`.')
        sys.exit(1)
      else:
        return xmlrunner.XMLTestRunner(output=output).run(master_suite)
    return unittest.TextTestRunner(stream=output or sys.stdout, verbosity=verbosity, **kwargs).run(master_suite)


def clirunner(arguments):

  '''  '''

  output, format = None, 'text'

  if arguments:
    if len(arguments) > 2:
      print "Can only call with a maximum of 2 arguments: FORMAT and OUTPUT, or just FORMAT."
      sys.exit(1)
    if len(arguments) == 2:
      format, output = tuple(arguments)
    else:
      format = arguments[0]

  try:
    run(output=output or (sys.stdout if format is 'text' else None), format=format)
  except:
    sys.exit(1)
  else:
    sys.exit(0)
