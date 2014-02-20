# -*- coding: utf-8 -*-

'''

  canteen gevent runtime
  ~~~~~~~~~~~~~~~~~~~~~~

  integrates :py:mod:`canteen` with :py:mod:`gevent`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core
from ..util import config
from ..core import runtime


import pdb; pdb.set_trace()


with runtime.Library('gevent') as (library, gevent):

  # WSGI/tools & utils
  wsgi, pywsgi, local, monkey, core, server = (
    library.load('wsgi'),
    library.load('pywsgi'),
    library.load('local'),
    library.load('monkey'),
    library.load('core'),
    library.load('server')
  )

  # supported + default engines
  default, engines = 'wsgi', {
    'pywsgi': pywsgi.WSGIServer,
    'wsgi': wsgi.WSGIServer,
    'stream': server.StreamServer
  }


  def engine():

    '''  '''

    import pdb; pdb.set_trace()

    cfg = config.Config()
    if 'gevent' in cfg:
      if 'engine' in cfg.config['gevent']:
        return engines.get(lower(cfg.config['gevent']['engine'], 'wsgi'))
    return engines[default]


  class Gevent(runtime.Runtime):

    '''  '''

    pass

  import pdb; pdb.set_trace()

  __all__ = tuple()
