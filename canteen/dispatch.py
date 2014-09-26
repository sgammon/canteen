# -*- coding: utf-8 -*-

"""

  dispatch
  ~~~~~~~~

  WSGI dispatch entrypoint. INCEPTION.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import os


## Globals
app = None


def spawn(app,
          config=None):  # pragma: no cover

  """ Spawn a Canteen app, suitable for dispatch
      as a WSGI application.

      :param app: Canteen application to be spawned,
        usually passed as a Python module.

      :param config: Application configuration, in
        the form of a ``canteen.util.Config`` instance
        wrapping a dictionary of application config.

      :returns: Instance of ``canteen.Runtime`` that
        can be dispatched via WSGI and wraps the target
        ``app`` object.  """

  # canteen core & util
  from canteen.core import runtime
  from canteen.util import config as cfg

  if not config: config = cfg.Config()
  return runtime.Runtime.spawn(app).configure(config)


# @TODO(sgammon): wtf is root
def run(app=None,
        interface='127.0.0.1',
        port=8080,
        dev=True,
        config=None):  # pragma: no cover

  """ Run a lightweight development server via the
      currently-active runtime. Suitable for use
      locally, with no required parameters at all.

      :param app: Canteen application to be spawned,
        usually passed as a Python module.

      :param root: Unused. No fucking clue what this
        is but I'd guess it's the root filepath to the
        application. I hope it's not that, though,
        because that would break App Engine.

      :param interface: Network interface that should
        be bound to for the resulting lightweight HTTP
        server. Defaults to ``127.0.0.1``.

      :param port: Integer port number that should be
        bound to for the resulting lightweight HTTP
        server. Defaults to ``8080``.

      :param dev: Boolean flag indicating whether we
        should be running in debug mode or not. Controls
        various things like log output. Defaults to
        ``True`` as this method is only meant to be an
        easy way to put up a dev server.

      :returns: Nothing useful, as this blocks to
        serve requests forever and ever. """

  if 'CANTEEN_TESTING' in os.environ and os.environ['CANTEEN_TESTING'] in (
    'yep', '1', 'sure', 'ofcourse', 'whynot', 'yes', 'on'):
    return spawn(app, config or {})  # pragma: no cover
  return spawn(app, config or {}).serve(interface, port)
