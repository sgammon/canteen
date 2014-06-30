# -*- coding: utf-8 -*-

'''

  canteen: uwsgi runtime
  ~~~~~~~~~~~~~~~~~~~~~~

  integrates :py:mod:`canteen` with :py:mod:`uwsgi`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core
from . import werkzeug
from ..util import debug
from ..core import hooks
from ..core import runtime


try:

  with runtime.Library('uwsgi', strict=True) as (library, uwsgi):

    class uWSGI(werkzeug.Werkzeug):

      '''  '''

      @property
      def logging(self):

        '''  '''

        return debug.Logger(self.__class__.__name__)

      @hooks.HookResponder('rpc-register', context=('service', 'method'))
      def register_rpc(self, service, method):

        '''  '''

        self.logging.info("%s -> %s" % (service.__class__.__name__, method.__name__))


    uWSGI.set_precedence(True)  # if we make it here, we're running *inside* uWSGI

except ImportError:
  pass

__all__ = tuple()
