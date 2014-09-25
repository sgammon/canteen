# -*- coding: utf-8 -*-

"""

  cli tests
  ~~~~~~~~~

  tests for canteen's data structures utilities.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# canteen
from canteen.util import cli
from canteen import FrameworkTest


class CLIToolsTests(FrameworkTest):

  """ Tests for `cli.Tool` """

  def test_construct(self):

    """ Test construction of a simple CLI tool """

    class Sample(cli.Tool):

      """ sample CLI tool """

      def execute(arguments):

          """ execution flow """

    assert isinstance(Sample.__dict__['execute'], staticmethod), (
      "by default tool execution methods should be static")
    return Sample

  def test_construct_subtool(self):

    """ Test construction of a CLI tool with subtools """

    class Sample(cli.Tool):

      """ sample CLI tool """

      class Subsample(cli.Tool):

        """ sub-sample CLI tool """

        @classmethod
        def execute(cls, arguments):

            """ sample """

    assert isinstance(Sample.Subsample.__dict__['execute'], classmethod), (
      "classmethods should be allowed as tool execution flows, instead got"
      " '%s'" % repr(Sample.Subsample.execute))
    return Sample

  def test_construct_arguments(self):

    """ Test construction of a CLI tool with arguments without short options """

    class Sample(cli.Tool):

      """ sample CLI tool """

      arguments = (
        ('--debug', {'action': 'store_true'}),)

      class Subsample(cli.Tool):

        """ sub-sample CLI tool """

        def execute(arguments):

            """ sample """

    return Sample

  def test_construct_arguments_with_short(self):

    """ Test construction of a CLI tool with arguments with short options """

    class Sample(cli.Tool):

      """ sample CLI tool """

      arguments = (
        ('--debug', '-d', {'action': 'store_true'}),)

      class Subsample(cli.Tool):

        """ sub-sample CLI tool """

        def execute(arguments):

            """ sample """

    return Sample

  def test_initialize_clitool(self):

    """ Test initializing a CLI tool in various contexts without safe mode """

    self.test_construct()(autorun=False, safe=False)
    self.test_construct_subtool()(autorun=False, safe=False)
    self.test_construct_arguments()(autorun=False, safe=False)
    self.test_construct_arguments_with_short()(autorun=False, safe=False)

  def test_initialize_clitool_safe(self):

    """ Test initializing a CLI tool in various contexts with safe mode """

    self.test_construct()(autorun=False, safe=True)
    self.test_construct_subtool()(autorun=False, safe=True)
    self.test_construct_arguments()(autorun=False, safe=True)
    self.test_construct_arguments_with_short()(autorun=False, safe=True)
