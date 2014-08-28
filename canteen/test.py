# -*- coding: utf-8 -*-

"""

  tests
  ~~~~~

  utilities for providing unittest functionality.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

from __future__ import print_function


if __debug__:

  # stdlib
  import os
  import sys
  import unittest

  # internals
  from .core import meta
  from .core import Library
  from .util import config
  from .util import ObjectProxy

  # dispatch tools
  from .dispatch import spawn

  # HTTP logic
  from .logic.http import semantics


  class BaseTest(unittest.TestCase):

    """  """

    __appconfig__ = None  # class-level assignment of app config state

    @classmethod
    def set_config(cls, target):

      """  """

      cls.__appconfig__ = target  # assign at class-level


    with Library('werkzeug', strict=True) as (library, werkzeug):

      __werkzeug__ = ObjectProxy({
        'test': library.load('test'),
        'testapp': library.load('testapp'),
        'wrappers': library.load('wrappers')
      })

      def _dispatch_endpoint(self):

        """  """

        return spawn(None, dev=True, config=config.Config(**self.__appconfig__))

      def _spawn_client(self, wsgi_target=None):

        """  """

        return self.__werkzeug__.test.Client(*(
          wsgi_target or self.__werkzeug__.testapp.test_app,
          semantics.HTTPSemantics.HTTPResponse))

      def dispatch(self, app, method, *args, **kwargs):

        """  """

        return getattr(self._spawn_client(app), method.lower())(*args, **kwargs)

      def GET(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'GET'))

      def POST(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'POST'))

      def HEAD(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'HEAD'))

      def OPTIONS(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'OPTIONS'))

      def PUT(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'PUT'))

      def DELETE(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'DELETE'))

      def TRACE(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'TRACE'))

      def PATCH(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'PATCH'))

      def CONNECT(self, *args, **kwargs):

        """  """

        return self.dispatch(*(
          kwargs.get('app', self._dispatch_endpoint()),
          'CONNECT'))


  class AppTest(BaseTest):

    """  """

    __root__, __owner__, __metaclass__ = True, 'AppTest', meta.Proxy.Registry


  class FrameworkTest(BaseTest):

    """  """

    __root__, __owner__, __metaclass__ = (
      True, 'FrameworkTest', meta.Proxy.Registry)


  def run(output=None,
          suites=None,
          scope=(AppTest, FrameworkTest),
          format='text',
          verbosity=1, **kwargs):  # pragma: nocover

    """  """

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

      """  """

      if not suite.countTestCases():
        return False
      return True

    _seen_tests = set()

    def merge_suite(left, right):

      """  """

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

    master_suite = unittest.TestSuite(reduce(merge_suite, (
      filter(filter_suite, master_suite))))

    # allow for XML format
    if format == 'xml':
      if output is None:
        output = ".develop/tests"
      try:
        import xmlrunner
      except ImportError:
        raise RuntimeError('Cannot generate XML output without `xmlrunner`.')
      else:
        return xmlrunner.XMLTestRunner(output=output).run(master_suite)
    runner = unittest.TextTestRunner(stream=output or sys.stdout,
                                     verbosity=verbosity, **kwargs)
    return runner.run(master_suite)


  def clirunner(arguments, root=None):  # pragma: nocover

    """  """

    output, format = None, 'text'

    if not __debug__:
      raise RuntimeError('Cannot run tests with -O or -OO.')
    if not root:
      root = os.getcwd()

    if arguments:
      if len(arguments) > 2:
        print("Can only call with a maximum of 2 arguments:"
              " FORMAT and OUTPUT, or just FORMAT.")
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
        'verbosity': 5 if 'TEST_VERBOSE' in os.environ else (
          0 if 'TEST_QUIET' in os.environ else 1)
      })
    except Exception as e:
      print(e)
      sys.exit(1)
    else:
      sys.exit(0)
