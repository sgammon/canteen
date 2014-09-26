# -*- coding: utf-8 -*-

"""

  CLI utils
  ~~~~~~~~~

  toolset for making command-line based tools. useful in general,
  particularly useful in making app management utilities.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""


# stdlib
import sys
import argparse
import textwrap


## Globals
_root_tool = None


## == Embedded Metaclass == ##
class Tool(object):

  """ Meta parent class that applies an embedded metaclass to enforce/ transform
      encapsulated objects into :py:mod:`argparse` directives. """

  safe = False  # parse only known arguments
  parser = None  # local parser for this tool
  autorun = False  # should we auto-run parse?
  commands = None  # subcommands to this tool
  arguments = None  # arguments for this tool

  class __metaclass__(type):

    """ Bound utility metaclass that re-writes embedded comand classes
        on-the-fly, into :py:mod:`argparse`-provided objects. """

    tree = {}  # command parser tree
    parsers = {}  # all encountered parsers

    def __new__(mcs, name, bases, properties):

      """ Check to see if we're initializing a new subcommand class, and if we
          are, construct the appropriate subparser.

          :param name: Target class name.
          :param bases: Target class bases.
          :param properties: Class dict properties.

          :raises RuntimeError: If invalid tool bindings are expressed in a
            meta-initialized class (for instance, an argument without a name).

          :returns: Initialized class, transformed into additional objects
            provided by :py:mod:`argparse`. """

      # initialize `Tool` regularly to apply this metaclass downwards
      if name == 'Tool': return super(mcs, mcs).__new__(*(
                                    mcs, name, bases, properties))

      _subtools, _arguments = [], []
      for key, value in properties.viewitems():

        # is it a list of arguments?
        if isinstance(value, (list, tuple)) and key is 'arguments':

          def _add_argument(_parser, _flag, _cfg):  # pragma: no cover
            if isinstance(_flag, tuple):
              return _parser.add_argument(*_flag, **_cfg)
            return _parser.add_argument(_flag, **_cfg)

          for bundle in value:
            if len(bundle) == 2:
              _name, _config = bundle
              _arguments.append((_add_argument, _name, _config))
            else:
              if isinstance(bundle[-1], dict):
                positional, _config = bundle[0:-1], bundle[-1]
                _arguments.append((_add_argument, positional, _config))

        # is it a subtool?
        elif isinstance(value, type) and issubclass(value, Tool):

          def _add_subparser(root, obj, subparsers):  # pragma: no cover
            ## bind helptext from __doc__
            sub = subparsers.add_parser((getattr(obj, 'name') if (
              hasattr(obj, 'name')) else obj.__name__).lower(), **{
                'conflict_handler': 'resolve',
                'help': textwrap.dedent(getattr(obj, '__doc__').strip()) if (
                hasattr(obj, '__doc__') and (
                  getattr(obj, '__doc__') is not None)) else None})

            sub.set_defaults(func=obj.execute)
            return sub

          _subtools.append((value, _add_subparser))

        elif not key.startswith('__'):

          if not isinstance(value, classmethod) and callable(value):
            properties[key] = staticmethod(value)
          else:
            # let it through if it's marked as a classmethod
            properties[key] = value

      # construct class
      klass = super(mcs, mcs).__new__(mcs, name, bases, properties)

      # add to registered parsers
      mcs.parsers[name] = {
        'name': (properties['name'] if 'name' in properties else name).lower(),
        'description': textwrap.dedent(properties['__doc__']) if (
          '__doc__' in properties) else None,
        'implementation': klass,
        'objects': {
          'subtools': _subtools,
          'arguments': _arguments}}

      return klass

  def __init__(self, parser=None, autorun=False, safe=False):

    """ This initializer method is called at the tip of the toolchain tree
        (composed of :py:class:`Tool` classes) to start the process of
        initializing and constructing each :py:mod:`argparse` object.

        Execution cascades from the tip to sub- :py:class:`Tool`s, and then to
        arguments.

        :param parser: Existing ``argparse.ArgumentParser`` to use for parsing
          config arguments, or ``None`` if one should be created on-the-fly.

        :param autorun: ``bool`` flag indicating that the CLI tool should start
          up and try to parse flags immediately.

        :param safe: ``bool`` flag indicating that we should only parse and
          consider flags *explicitly defined* by the CLI tool, rather than
          letting through unknown flags. """

    global _root_tool

    self.autorun, self.safe = autorun, safe

    # lookup local config
    config = self.__metaclass__.parsers[self.__class__.__name__]

    if not parser:
      # start top-level argument parser
      parser = argparse.ArgumentParser(prog=(self.name if (
        hasattr(self, 'name')) else self.__class__.__name__).lower(),
        description=textwrap.dedent(self.__doc__.strip()) if not (
          (sys.flags.optimize > 1)) else '')
      if not _root_tool: _root_tool = parser

    self.parser = parser  # assign local parser

    # local args
    for _callable, flag, _config in (
      config.get('objects', {}).get('arguments', [])):
      _callable(parser, flag, _config)  # initialize each argument

    # local subtools
    if config.get('objects', {}).get('subtools', []):
      commands = parser.add_subparsers(dest='subcommand', title='bundled tools')
      for impl, _callable in config.get('objects', {}).get('subtools', []):
        subparser = _callable(_root_tool, impl, commands)  # initialize subtools
        setattr(self, (impl.name if (
          hasattr(impl, 'name')) else impl.__name__).lower(), impl(subparser))

    if autorun and safe:  # pragma: no cover
      self(*_root_tool.parse_known_args())
    elif autorun:  # pragma: no cover
      self(_root_tool.parse_args())

  @classmethod
  def execute(cls, arguments):  # pragma: no cover

    """ Execute the local ``Tool`` subclass against command-line-style args
        at ``arguments``, which are passed in from ``argparse``.

        :param arguments: Arguments object passed-in from ``argparse``, as an
          instance of :py:class:`argparse.Namespace`, resulting from a call to
          ``parser.parse_args``.

        :return: Must return a truthy value (such as ``True``) to indicate that
          whatever operation was requested completed successfully, or a falsy
          value otherwise (such as ``False``). Failure values produce a Unix
          exit code of ``1`` when running on the CLI, versus a code ``0`` for
          success/truthy values. """

    raise NotImplementedError('Command line tool "%s"'
                              ' is not implemented.' % repr(cls))

  def __call__(self, arguments, unknown=None):  # pragma: no cover

    """ Begins dispatching execution from a set of parsed arguments, as the
        product of a :py:meth:`parser.parse_args()` call.

        :param arguments: :py:class:`argparse.Namespace` object, resulting from
          ``parser.parse_args()``.

        :param unknown:

        :returns: Unix return code, suitable for passing directly to
          ``sys.exit()``. """

    try:
      # is it a subtool?
      if hasattr(arguments, 'func'):
        ## dispatch and return
        if self.safe:
          return_value = arguments.func(arguments, unknown)
        else:
          return_value = arguments.func(arguments)
      else:
        # no? ok
        if self.safe:
          return_value = self.execute(arguments, unknown)
        else:
          return_value = arguments.func(arguments)

    except Exception:
      raise
    return 1 if not return_value else 0
