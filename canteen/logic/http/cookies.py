# -*- coding: utf-8 -*-

"""

  HTTP cookie logic
  ~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import json

# core runtime
from canteen.base import logic
from canteen.core import runtime

# canteen utils
from canteen.util import decorators

# core session API
from ..session import SessionEngine


with runtime.Library('werkzeug', strict=True) as (library, werkzeug):

  # subimports
  securecookie = library.load('contrib.securecookie')


  @decorators.bind('http.cookies')
  class Cookies(logic.Logic):

    """  """

    __modes__ = {}  # modes for dealing with cookies

    @classmethod
    def add_mode(cls, name):

      """  """

      def _mode_adder(mode_klass):

        """  """

        cls.__modes__[name] = mode_klass
        cls.__default__ = cls.__modes__[name]
        return mode_klass

      return _mode_adder

    @classmethod
    def get_mode(cls, name):

      """  """

      return cls.__modes__[name] if name in cls.__modes__ else cls.__default__


    @SessionEngine.configure('cookies')
    class CookieSessions(SessionEngine):

      """  """

      def load(self, request, http):

        """  """

        # if there is a session cookie, load it...
        if self.config.get('key', 'canteen') in request.cookies:

          # resolve serializer
          _serializer = Cookies.get_mode(self.config.get('mode', 'json'))

          # unserialize the cookie
          session = _serializer.unserialize(*(
            request.cookies[(
              self.config.get('key', 'canteen'))], self.api.secret))

          if not session.new: return request.set_session(session, self)

        # set an explicitly-empty session (none was found)
        return request.set_session(None, self)

      def commit(self, request, response, session):

        """  """

        # resolve serializer
        _serializer, _key = (
          Cookies.get_mode(self.config.get('mode', 'json')),
          self.config.get('key', 'canteen')
        )

        # serialize the cookie
        serialized = _serializer({
          'uuid': session.id
        }, self.api.secret).serialize()

        # do we even need to write the cookie?
        if _key in request.cookies and (request.cookies[_key] == serialized):
          return  # the cookies are equal: don't need to re-set it

        # cookie parameters
        _params = {}

        # resolve expiration
        if 'max_age' not in self.config:
          if 'expires' not in self.config:
            _params['max_age'] = None  # expire on session close
          else:
            _params['expires'] = self.config['expires']
        else:
          _params['max_age'] = self.config['max_age']

        # copy-over cookie params
        _params.update({
          'path': self.config.get('path', '/'),
          'secure': self.config.get('secure', False),
          'domain': self.config.get('domain', request.host.split(':')[0]),
          'httponly': self.config.get('http_only', (
                        self.config.get('httponly', False)))
        })

        # write cookie into the response
        response.set_cookie(_key, serialized, **_params)


  @Cookies.add_mode('json')
  class JSONCookie(securecookie.SecureCookie):

    """  """

    class CookieSerializer(json.JSONEncoder):

      """  """

      @classmethod
      def dumps(cls, structure):

        """  """

        return cls().encode(structure)

      @classmethod
      def loads(cls, serialized):

        """  """

        return json.loads(serialized)

      def default(self, obj):

        """  """

        if isinstance(obj, Exception):
          if hasattr(obj, 'message'):
            return obj.message

        return json.JSONEncoder.default(self, obj)

    serialization_method = CookieSerializer


  with runtime.Library('flask') as (flib, flask):

    # load flask sessions
    flask_sessions = flib.load('sessions')


    class FlaskSessionBridge(JSONCookie, flask_sessions.SessionMixin):
        """  """

    # install our session bridge, forcing Flask to use JSON cookies
    flask_sessions.SecureCookieSessionInterface.session_class = (
      FlaskSessionBridge)
