# -*- coding: utf-8 -*-

"""

  page base
  ~~~~~~~~~

  ``Page``s represnt the simplest way to respond to an HTTP request in Canteen.
  They are inherently bound to HTTP, in that you specify methods directly from
  the HTTP spec to be executed when the corresponding method is requested.

  Example:

    # -*- coding: utf-8 -*-
    from canteen import url, Page

    @url('/')
    class Home(Page):


  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# DI & util
from . import handler


class Page(handler.Handler):

  """ Extendable class exposed to developers to prepare a class that responds to
      particular HTTP requests. Great way to return static content or render
      templates, as ``Page``s come preconfigured for use with :py:mod:`Jinja2`
      and Canteen's builtin logic (session, static asset and caching tools). """

  __owner__ = "Page"
