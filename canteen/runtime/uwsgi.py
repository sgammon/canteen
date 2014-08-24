# -*- coding: utf-8 -*-

'''

  uwsgi runtime
  ~~~~~~~~~~~~~

  integrates :py:mod:`canteen` with :py:mod:`uwsgi`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core + util
from ..util import debug
from ..util import decorators
from ..core import hooks, runtime


try:  # pragma: no cover

  with runtime.Library('uwsgi', strict=True) as (library, uwsgi):

    # logger
    logging = debug.Logger('uWSGI')


    @decorators.bind('uwsgi')
    class uWSGI(runtime.Runtime):

      '''  '''

      @classmethod
      def register_rpc(cls, method):

        '''  '''

        pass  # @TODO(sgammon): register methods


    # if we make it here, we're running *inside* uWSGI
    uWSGI.set_precedence(True)

except ImportError:
  pass
