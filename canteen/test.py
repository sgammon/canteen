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


  class AppTest(unittest.TestCase):

    '''  '''

    __root__, __owner__, __metaclass__ = True, 'AppTest', meta.Proxy.Registry


  class FrameworkTest(unittest.TestCase):

    '''  '''

    __root__, __owner__, __metaclass__ = True, 'FrameworkTest', meta.Proxy.Registry


  def run(output, scope=(AppTest, FrameworkTest), format='text', verbosity=5, **kwargs):

    '''  '''

    # fill testsuite with found testcases
    suite = unittest.TestSuite()
    for bucket in scope:
      for child in meta.Proxy.Registry.children(bucket):
        suite.loadTestsFromTestCase(child)

    # allow for XML format
    if format is 'xml':
      try:
        import xmlrunner
      except ImportError:
        raise RuntimeError('Cannot generate XML output without `xmlrunner`.')
        sys.exit(1)
      else:
        return xmlrunner.XMLTestRunner(output=output).run(suite)
    return unittest.TestRunner(output=output, verbosity=verbosity, **kwargs).run(suite)
