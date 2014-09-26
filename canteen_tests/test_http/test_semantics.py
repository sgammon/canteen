# -*- coding: utf-8 -*-

"""

  HTTP semantic logic tests
  ~~~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# testing
from canteen import test
from canteen import base

# HTTP layer
from canteen.logic import http

# werkzeug
from werkzeug import routing, wrappers
from werkzeug.test import EnvironBuilder


class URLUtilTests(test.FrameworkTest):

  """ Tests builtin framework decorator for binding URLs """

  def _mock_handler(self):

    """ Generate a small mock object that can be introspected.

        :returns: An object. """

    return object()

  def test_url_basic(self):

    """ Test basic functionality of `http.url` decorator """

    sent = wrap = self._mock_handler()
    out = http.url(r'/sup')(wrap)
    assert out is sent is wrap

  def test_url_named(self):

    """ Test creating a named `http.url` binding """

    sent = wrap = self._mock_handler()
    out = http.url('test', r'/sup')(wrap)
    assert out is sent is wrap

  def test_url_param(self):

    """ Test creating a bound `http.url` with params in the URL """

    sent = wrap = self._mock_handler()
    out = http.url('test', r'/sup/<int:num>')(wrap)
    assert out is sent is wrap

  def test_url_wrap(self):

    """ Test the `http.url` decorator for `wrap` keyword usage """

    sent = wrap = self._mock_handler()

    def other_wrap(target):
      assert target is sent is wrap
      return target

    out = http.url('test', r'/sup', wrap=other_wrap)(wrap)
    assert out is sent is wrap


class HTTPSemanticsTests(test.FrameworkTest):

  """ Tests builtin framework logic related to HTTP semantics. """

  def _mock_environ(self, *args, **kwargs):

    """ Make a small mock WSGI environment. """

    return EnvironBuilder(*args, **kwargs).get_environ()

  def test_construct(self):

    """ Test constructing an instance of `HTTPSemantics` """

    h = http.HTTPSemantics()
    return h

  def test_injection(self):

    """ Test injection of `HTTPSemantics` on DI consumers """

    b = base.Handler({}, lambda: None)
    assert b.http

  def test_http_request(self):

    """ Test constructing an instance of `HTTPRequest` """

    r = http.HTTPSemantics.new_request(self._mock_environ())
    assert r
    assert isinstance(r, http.HTTPSemantics.HTTPRequest)
    return r

  def test_http_request_set_session(self):

    """ Test setting the current session by force on an `HTTPRequest` """

    session = {'user': 123}
    request = self.test_http_request()
    request.set_session(session)

    assert isinstance(request.session, tuple)
    assert len(request.session) == 2

  def test_http_response(self):

    """ Test constructing an instance of `HTTPResponse` """

    r = http.HTTPSemantics.new_response()
    assert r
    assert isinstance(r, http.HTTPSemantics.HTTPResponse)
    return r

  def test_add_route(self):

    """ Test force-adding a bound URL via `HTTPSemantics` """

    http.HTTPSemantics.add_route((r'/never-ever', 'testing'), lambda: 'hi')

  def test_resolve_route(self):

    """ Test resolving a route by name via `HTTPSemantics` """

    self.test_add_route()
    r = http.HTTPSemantics.resolve_route('testing')
    assert r

    r = http.HTTPSemantics.resolve_route('idonotexistnotever')
    assert not r

  def test_routes_iter(self):

    """ Test iterating through known URL routes via `HTTPSemantics` """

    for route in http.HTTPSemantics.routes:
      assert route
      assert isinstance(route, routing.Rule)

  def test_route_map(self):

    """ Test generating a route map via `HTTPSemantics` """

    assert http.HTTPSemantics.route_map
    assert isinstance(http.HTTPSemantics.route_map, routing.Map)

  def test_http_error(self):

    """ Test raising an HTTP error via `HTTPSemantics` """

    with self.assertRaises(http.HTTPSemantics.HTTPException):
      http.HTTPSemantics.error(404)

    with self.assertRaises(http.HTTPSemantics.HTTPException):
      http.HTTPSemantics.error(500)

  def test_http_redirect(self):

    """ Test preparing an HTTP redirect via `HTTPSemantics` """

    r = http.HTTPSemantics.redirect('/sample')
    assert isinstance(r, wrappers.Response)
