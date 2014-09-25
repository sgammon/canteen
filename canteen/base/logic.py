# -*- coding: utf-8 -*-

"""

  logic base
  ~~~~~~~~~~

  Provides base configuration and code to setup Canteen ``Logic`` classes, which
  allow a developer to provide a piece of cross-cutting functionality to their
  entire application.

  ``Logic`` classes are Canteen ``Component``s, meaning they provide injectable
  structures for the DI engine. ``Logic`` classes, when bound to a string name
  with ``decorators.bind``, will be accessible from ``Compound`` object methods
  at ``self.name``.

  Example:

    # -*- coding: utf-8 -*-
    from canteen import decorators, Logic

    @decorators.bind('math')
    class Math(Logic):


  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# core API
from ..core import meta
from ..util import decorators


@decorators.singleton
class Logic(object):

  """ Base class for Canteen ``Logic`` components. Specifies a class tree on the
      ``Proxy.Component`` side (meaning that it *provides* DI resources, instead
      of a ``Proxy.Compound``, which *consumes* them).

      ``Logic`` classes must be bound using the ``decorators.bind`` tool, which
      takes a ``str`` name and binds a ``Logic`` class (or child) to that name
      on all ``Compound`` classes and objects. """

  __owner__, __metaclass__ = "Logic", meta.Proxy.Component
