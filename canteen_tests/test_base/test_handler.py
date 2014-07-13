# -*- coding: utf-8 -*-

'''

  base handler tests
  ~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# testing
from canteen import test

# base handler
from canteen.core import runtime
from canteen.base import handler

# mock objects
from werkzeug import test as wtest
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response
from werkzeug.exceptions import MethodNotAllowed


class BaseHandlerTest(test.FrameworkTest):

  ''' Tests for :py:mod:`canteen.base.handler`. '''

  def _make_handler(self, valid=False, _impl=handler.Handler, _environ=None):

    ''' Mock up a quick `Handler` object. '''

    if not valid:  # don't need valid WSGI internals?
      environ, callback, _runtime, request, response = (
        {'sample': 'hi'}, lambda: True, runtime.Runtime(object()),
        object(), object()
      )

      # allow environ overrides
      if _environ: environ.update(_environ)

      canteen_style = _impl(*(
        environ, callback, _runtime, request, response))
      return canteen_style, request, response, _runtime

    result, environ = (
      {},
      wtest.create_environ('/sample', 'http://localhost:8080/')
    )

    # allow environ overrides
    if _environ: environ.update(_environ)

    callback, _runtime, request, response = (
      lambda status, headers: (
        result.__setitem__('status', status) and
        result.__setitem__('headers', headers)),
      runtime.Runtime(object()),
      Request(environ),
      Response()
    )

    canteen_style = _impl(*(
      environ,
      callback,
      _runtime,
      request,
      response
    ))

    return canteen_style, request, response, runtime

  def test_base_handler(self):

    ''' Test that `Handler` is exposed for import '''

    assert hasattr(handler, 'Handler')

  def test_construct_handler(self):

    ''' Test various constructions of `Handler` '''

    ## try WSGI-style construction
    environ = {'sample': 'hi'}
    callback = lambda: True

    wsgi_style = handler.Handler(environ, callback)
    assert hasattr(wsgi_style, 'environ')
    assert hasattr(wsgi_style, 'environment')
    assert wsgi_style.environ['sample'] == 'hi'
    assert wsgi_style.callback() is True
    assert wsgi_style.start_response() is True

    ## try canteen-style construction
    canteen_style, request, response, runtime = self._make_handler()
    assert hasattr(canteen_style, 'environ')
    assert hasattr(canteen_style, 'environment')
    assert canteen_style.environ['sample'] == 'hi'
    assert canteen_style.callback() is True
    assert canteen_style.start_response() is True
    assert canteen_style.request is request
    assert canteen_style.response is response
    assert canteen_style.runtime is runtime

  def test_template_context(self):

    ''' Test `Handler.template_context` '''

    handler, request, response, runtime = self._make_handler()
    context = handler.template_context

    # test top-level stuff
    for entry in (
      'handler', 'config', 'runtime', 'http', 'wsgi', 'cache',
      'asset', 'services', 'output', 'link', 'route'):
      assert entry in context, "%s not found in template context" % entry

    # base, HTTP and WSGI
    assert context['handler'] is handler
    assert context['runtime'] is runtime
    assert isinstance(context['config'], dict)
    assert context['wsgi']['callback']() is True
    assert context['http']['request'] is request
    assert context['wsgi']['callback']() is True
    assert context['http']['response'] is response
    assert context['wsgi']['start_response']() is True
    assert context['wsgi']['environ']['sample'] == 'hi'

    # links and routes
    assert callable(context['link'])
    assert callable(context['route']['build'])
    assert callable(context['route']['resolve'])

  def test_respond(self):

    ''' Test `Handler.respond` interface '''

    handler, request, response, runtime = self._make_handler(True)

    content = '<b>hi i am content</b>'
    handler.respond(content)

    assert handler.status is 200
    assert handler.response.response == content
    assert handler.response.status_code is 200

  def test_dispatch(self):

    ''' Test `Handler` __call__ dispatch '''

    content = '<b>hi sup</b>'

    class SubHandler(handler.Handler):

      ''' I am an example handler '''

      def GET(self):

        ''' I am an example GET method '''

        self.get_called = True
        self.respond(content)

    _handler, request, response, runtime = self._make_handler(True, SubHandler)
    response = _handler({})

    assert _handler.get_called
    assert response.status_code is 200
    assert response.response == content

  def test_dispatch_direct(self):

    ''' Test `Handler` direct __call__ dispatch '''

    content = '<b>hi sup</b>'

    class SubHandler(handler.Handler):

      ''' I am an example handler '''

      def GET(self):

        ''' I am an example GET method '''

        self.get_called = True
        self.respond(content)

    _handler, request, response, runtime = self._make_handler(True, SubHandler)
    response = _handler({}, direct=True)

    assert response is _handler
    assert _handler.status is 200
    assert _handler.response.status_code is 200
    assert _handler.response.response == content

  def test_prepare_hook(self):

    ''' Test that `Handler.prepare` is called before dispatch '''

    content = '<b>hi sup</b>'

    class SubHandler(handler.Handler):

      ''' I am an example handler '''

      def prepare(self, url_args, direct):

        ''' I prepare things '''

        self.prepare_tripped = True

      def GET(self):

        ''' I am an example GET method '''

        if self.prepare_tripped:
          self.get_called = True
        self.respond(content)

    _handler, request, response, runtime = self._make_handler(True, SubHandler)
    response = _handler({})

    assert response.status_code is 200
    assert response.response == content
    assert _handler.prepare_tripped is True
    assert _handler.get_called is True

  def test_destroy_hook(self):

    ''' Test that `Handler.destroy` is called after dispatch '''

    content = '<b>hi sup</b>'

    class SubHandler(handler.Handler):

      ''' I am an example handler '''

      def GET(self):

        ''' I am an example GET method '''

        self.get_called = True
        self.respond(content)

      def destroy(self, response):

        ''' I prepare things '''

        if self.get_called:
          self.destroy_tripped = True

    _handler, request, response, runtime = self._make_handler(True, SubHandler)
    response = _handler({})

    assert response.status_code is 200
    assert response.response == content
    assert _handler.destroy_tripped is True
    assert _handler.get_called is True

  def test_response_return(self):

    ''' Test that `Handler.GET/POST/etc` can return a response '''

    content = '<b>hi sup</b>'
    alt_content = '<b>goodbye_friend</b>'

    class SubHandler(handler.Handler):

      ''' I am an example handler '''

      def GET(self):

        ''' I am an example GET method '''

        self.respond(content)
        return alt_content  # cancels internal response

    _handler, request, response, runtime = self._make_handler(True, SubHandler)
    response = _handler({})

    assert response == alt_content

  def test_invalid_method(self):

    ''' Test calling an invalid method on `Handler` (should raise HTTP405) '''

    class SubHandler(handler.Handler):

      ''' I am an example handler '''

      def GET(self):

        ''' I am an example GET method '''

        pass

    _handler, request, response, runtime = self._make_handler(
      True,
      SubHandler,
      _environ={'REQUEST_METHOD': 'POST'})

    with self.assertRaises(MethodNotAllowed):
      _handler({})
