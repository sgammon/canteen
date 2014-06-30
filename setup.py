# -*- coding: utf-8 -*-

'''

  canteen: setup
  ~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# setuptools
import sys, logging, setuptools as tools; dependencies = []


## Constants
SETUPTOOLS_VERSION = '4.0.1'  # version of setuptools needed for a pleasant life
HAMLISH_VERSION, PROTOBUF_VERSION = '0.3.4-canteen', '2.5.2-canteen'   # custom version to forcefail pypi
VERSION_FLOAT = lambda version: float('.'.join(version.split('.')[0:1]))  # extract float of major version in X.X[.X]
CHECK_SETUPTOOLS = lambda: CURRENT_SETUPTOOLS_VERSION <= SETUPTOOLS_VERSION  # check version of setuptools
CURRENT_SETUPTOOLS_VERSION = VERSION_FLOAT(getattr(tools, '__version__', '0.0.0'))  # extract current seutptools version

## Logging
log = logging.getLogger('canteen.setup')
log_handler = logging.StreamHandler(sys.stdout)
log.addHandler(log_handler), log.setLevel(logging.DEBUG if __debug__ else logging.WARNING)

try:
  from colorlog import ColoredFormatter
except ImportError:
  log.debug('No support found for `colorlog`. No colors for u.')
else:
  log_handler.setFormatter(ColoredFormatter(
    "%(log_color)s[%(levelname)s]%(reset)s %(message)s",
    datefmt=None, reset=True, log_colors={
      'DEBUG':    'cyan',
      'INFO':     'green',
      'WARNING':  'yellow',
      'ERROR':    'red',
      'CRITICAL': 'red'
    }))


## Environment checks
if not CHECK_SETUPTOOLS():
  log.warning('Setuptools out of date with version "%s", where'
                  'at least version "%s" is required. Attempting upgrade...' % (SETUPTOOLS_VERSION))
  dependencies.append('setuptools<=%s' % SETUPTOOLS_VERSION)

  try:
    # force update/download
    from ez_setup import use_setuptools
    use_setuptools()

    # reload module and check version
    reload(setuptools)
    CURRENT_SETUPTOOLS_VERSION = setuptools.__version__
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
  import protobuf
except ImportError:
  log.info('Protobuf not found. Adding custom version "%s"...' % PROTOBUF_VERSION)
  dependencies.append('protobuf==%s' % PROTOBUF_VERSION)

try:
  import hamlish_jinja
except ImportError:
  log.info('HamlishJinja requested but not found. Adding custom version "%s"...' % HAMLISH_VERSION)
  dependencies.append('hamlish_jinja==%s' % HAMLISH_VERSION)


tools.setup(name="canteen",
      version="0.2-alpha",
      description="Minimally complicated, maximally blasphemous approach to app development",
      author="Sam Gammon",
      author_email="sam@momentum.io",
      url="https://github.com/sgammon/canteen",
      packages=[
        "canteen",
        "canteen.base",
        "canteen.core",
        "canteen.core.api",
        "canteen.logic",
        "canteen.logic.http",
        "canteen.model",
        "canteen.model.adapter",
        "canteen.rpc",
        "canteen.rpc.protocol",
        "canteen.runtime",
        "canteen.util",
      ] + [
        "canteen_tests",
        "canteen_tests.test_adapters",
        "canteen_tests.test_core",
        "canteen_tests.test_model",
        "canteen_tests.test_util",
      ] if __debug__ else [],
      install_requires=([
        "jinja2",
        "werkzeug",
        "protorpc"
      ] + dependencies),
      dependency_links=(
        "git+git://github.com/sgammon/protobuf.git#egg=protobuf-%s" % PROTOBUF_VERSION,
        "git+git://github.com/sgammon/hamlish-jinja.git#egg=hamlish_jinja-%s" % HAMLISH_VERSION
      ),
      tests_require=("nose",)
)
