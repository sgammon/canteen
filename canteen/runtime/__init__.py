# -*- coding: utf-8 -*-

"""

  runtime
  ~~~~~~~

  holds code that bridges :py:mod:`canteen` into various WSGI runtimes,
  like :py:mod:`gevent` and :py:mod:`wsgiref`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# runtimes
from . import uwsgi
from . import wsgiref
from . import werkzeug


__all__ = ('uwsgi',
           'wsgiref',
           'werkzeug')
