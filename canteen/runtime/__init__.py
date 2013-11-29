# -*- coding: utf-8 -*-

'''

  canteen runtime
  ~~~~~~~~~~~~~~~

  holds code that bridges :py:mod:`canteen` into various WSGI runtimes,
  like :py:mod:`gevent` and :py:mod:`wsgiref`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# runtimes
from . import gevent
from . import wsgiref

__all__ = ['gevent', 'wsgiref']
