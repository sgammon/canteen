# -*- coding: utf-8 -*-

'''

  cli tests
  ~~~~~~~~~

  tests for canteen's data structures utilities.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# canteen
from canteen.util import cli
from canteen import FrameworkTest


class CLIToolsTests(FrameworkTest):

  ''' Tests for `cli.Tool` '''

  def test_construct(self):

    ''' Test construction of a simple CLI tool '''

    class Sample(cli.Tool):

      ''' sample CLI tool '''

      def execute(arguments):

        ''' execution flow '''

    # if we get here, no error

  def test_construct_subtool(self):

    ''' Test construction of a CLI tool with subtools '''

    class Sample(cli.Tool):

      ''' sample CLI tool '''

      class Subsample(cli.Tool):

        ''' sub-sample CLI tool '''

        def execute(arguments):

          ''' sample '''

    # if we get here, no error

  def test_construct_arguments(self):

    ''' Test construction of a CLI tool with arguments '''

    class Sample(cli.Tool):

      ''' sample CLI tool '''

      arguments = (
        ('--debug', '-d', {'action': 'store_true'}),
      )

      class Subsample(cli.Tool):

        ''' sub-sample CLI tool '''

        def execute(arguments):

          ''' sample '''

    # if we get here, no error
