# -*- coding: utf-8 -*-

"""

  framework setup
  ~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""


if __debug__:

  # setuptools
  import sys
  import logging
  import traceback
  import setuptools as tools


  ## Constants / Globals

  dependencies = []

  # version of setuptools needed for a pleasant life
  SETUPTOOLS_VERSION = '4.0.1'

  # custom version to forcefail pypi
  HAMLISH_VERSION, PROTOBUF_VERSION = '0.3.4-canteen', '2.5.2-canteen'

  # extract float of major version in X.X[.X]
  VERSION = lambda version: float('.'.join(version.split('.')[0:1]))

  # check version of setuptools
  CHECK_SETUPTOOLS = lambda: CURRENT_SETUPTOOLS_VERSION <= SETUPTOOLS_VERSION

  # extract current seutptools version
  CURRENT_SETUPTOOLS_VERSION = VERSION(getattr(tools, '__version__', '0.0.0'))

  # git endpoint for customized protobuf (formats with version)
  PROTOBUF_GIT = "git+git://github.com/sgammon/protobuf.git" \
                 "#egg=protobuf-%s"

  # git endpoint for customized hamlish (formats with version)
  HAMLISH_GIT = "git+git://github.com/sgammon/hamlish-jinja.git" \
                "#egg=hamlish_jinja-%s"

  ## Logging
  log = logging.getLogger('canteen.setup')
  log_handler = logging.StreamHandler(sys.stdout)
  log.addHandler(log_handler), log.setLevel((
    logging.DEBUG if __debug__ else logging.WARNING))


  def prepare():  # pragma: no cover

    """ Prepare constants and tools for setting up Canteen.

        :returns: ``go``, a closured function that, when called, will begin
          framework setup. """

    try:
      from colorlog import ColoredFormatter
    except ImportError:  # pragma: no cover
      log.debug('No support found for `colorlog`. No colors for u.')
    else:  # pragma: no cover
      log_handler.setFormatter(ColoredFormatter(
        "%(log_color)s[%(levelname)s]%(reset)s %(message)s",
        datefmt=None, reset=True, log_colors={
          'DEBUG':    'cyan',
          'INFO':     'green',
          'WARNING':  'yellow',
          'ERROR':    'red',
          'CRITICAL': 'red'}))


    ## Environment checks
    if not CHECK_SETUPTOOLS():
      log.warning('Setuptoo¡s out of date with version "%s", where'
                  'at least version "%s" is required.'
                  ' Attempting upgrade...' % (SETUPTOOLS_VERSION))
      dependencies.append('setuptools<=%s' % SETUPTOOLS_VERSION)

      try:
        # force update/download
        from ez_setup import use_setuptools
        use_setuptools()

        # reload module and check version
        reload(tools)
        CURRENT_SETUPTOOLS_VERSION = tools.__version__
      except Exception as e:
        log.error('Encountered exception using `ez_setup`...')
        if __debug__:
          traceback.print_exc()

      # fail hard if no suitable options
      if not CHECK_SETUPTOOLS():
        log.error('Failed to find a suitable version of setuptools.'
                  ' Building without support for HAML or RPC.')
        sys.exit(1)

    try:
      import protorpc
    except ImportError:
      log.info('Protobuf not found.'
               ' Adding custom version "%s"...' % PROTOBUF_VERSION)
      dependencies.append('protobuf==%s' % PROTOBUF_VERSION)

    try:
      import hamlish_jinja
    except ImportError:
      log.info('HamlishJinja requested but not found.'
               ' Adding custom version "%s"...' % HAMLISH_VERSION)
      dependencies.append('hamlish_jinja==%s' % HAMLISH_VERSION)

    return lambda: tools.setup(

      # == info == #
      name="canteen",
      version="0.4-alpha",
      description="Minimally complicated, maximally blasphemous"
                  " approach to Python development",

      # == authorship == #
      author="Sam Gammon",
      author_email="sam@momentum.io",

      # == flags == #
      zip_safe=True,
      url="https://github.com/sgammon/canteen",

      # == package tree == #
      packages=["canteen",
                "canteen.base",
                "canteen.core",
                "canteen.logic",
                "canteen.logic.http",
                "canteen.model",
                "canteen.model.adapter",
                "canteen.rpc",
                "canteen.rpc.protocol",
                "canteen.runtime",
                "canteen.util"] +

               ["canteen_tests",
                "canteen_tests.test_adapters",
                "canteen_tests.test_base",
                "canteen_tests.test_core",
                "canteen_tests.test_http",
                "canteen_tests.test_model",
                "canteen_tests.test_rpc",
                "canteen_tests.test_util"] if __debug__ else [],

      # == dependencies == #
      install_requires=(["jinja2",
                         "werkzeug",
                         "protorpc"] + dependencies),

      # == test dependencies == #
      tests_require=("nose", "coverage", "fakeredis"),

      # == dependency links == #
      dependency_links=(
        PROTOBUF_GIT % PROTOBUF_VERSION,
        HAMLISH_GIT % HAMLISH_VERSION))
