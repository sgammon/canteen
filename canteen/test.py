# -*- coding: utf-8 -*-

'''

  canteen: tests
  ~~~~~~~~~~~~~~

  utilities for providing unittest functionality.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

if __debug__:


  # stdlib
  import os
  import sys
  import unittest

  # registry magic
  from .core import meta


  class AppTest(unittest.TestCase):

    '''  '''

    __root__, __owner__, __metaclass__ = True, 'AppTest', meta.Proxy.Registry


  class FrameworkTest(unittest.TestCase):

    '''  '''

    __root__, __owner__, __metaclass__ = True, 'FrameworkTest', meta.Proxy.Registry


  def run(output=None, suites=None, scope=(AppTest, FrameworkTest), format='text', verbosity=1, **kwargs):  # pragma: nocover

    '''  '''

    # fill testsuite with found testcases
    master_suite, loader = [], unittest.TestLoader()

    for bucket in scope:
      suite = unittest.TestSuite()

      for child in bucket.iter_children():
        suite.addTests(loader.loadTestsFromTestCase(child))

      master_suite.append(suite)

    if suites:
      for _suite in suites:
        master_suite.append(_suite)

    def filter_suite(suite):

      '''  '''

      if not suite.countTestCases():
        return False
      return True

    _seen_tests = set()

    def merge_suite(left, right):

      '''  '''

      _master = []
      for case in [test for test in left] + [test for test in right]:
        if isinstance(case, unittest.TestSuite):
          for _case in case:
            _master.append(_case)
            _seen_tests.add(_case)
          continue
        if case not in _seen_tests:
          _master.append(case)
          _seen_tests.add(case)
        continue
      return set(unittest.TestSuite(_master))

    master_suite = unittest.TestSuite(reduce(merge_suite, filter(filter_suite, master_suite)))

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


  def clirunner(arguments, root=None):  # pragma: nocover

    '''  '''

    output, format = None, 'text'

    if not __debug__:
      raise RuntimeError('Cannot run tests with -O or -OO.')
    if not root:
      root = os.getcwd()

    if arguments:
      if len(arguments) > 2:
        print "Can only call with a maximum of 2 arguments: FORMAT and OUTPUT, or just FORMAT."
        sys.exit(1)
      if len(arguments) == 2:
        format, output = tuple(arguments)
      else:
        format = arguments[0]

    discovered = None
    if root:
      loader = unittest.TestLoader()
      discovered = loader.discover(root)

    try:
      run(**{
        'output': output or (sys.stdout if format is 'text' else None),
        'suites': discovered,
        'format': format,
        'verbosity': 5 if 'TEST_VERBOSE' in os.environ else (0 if 'TEST_QUIET' in os.environ else 1)
      })
    except Exception as e:
      print e
      sys.exit(1)
    else:
      sys.exit(0)


  __all__ = (
    'AppTest',
    'FrameworkTest',
    'run',
    'clirunner'
  )
