# -*- coding: utf-8 -*-

"""

  session logic
  ~~~~~~~~~~~~~

  provides base logic for handling and enforcing user sessions.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""


# stdlib
import time, hashlib, abc
import random, string, operator

# core, base, util
from ..core import hooks
from ..base import logic
from ..util import config
from ..util import decorators
from .. import model as models


## Globals
_BUILTIN_SESSION_PROPERTIES = frozenset((
  'seen',
  'data',
  'csrf',
  'established',
  'seen',
  'agent',
  'client',
  'tombstoned'))


class ClientSession(models.Model):

  """ Canteen model for a user or HTTP client session. Tracks things like a
      session ID, last-seen-time, and when the session was established. """

  seen = int  # when this session was last seen
  data = dict  # attached session state data
  csrf = basestring  # token for use in a CSRF
  agent = basestring  # useragent string last seen from this session
  client = basestring  # IP address last seen from this session
  tombstoned = bool, {'default': False}  # flag for destroying session by force
  established = int, {'required': True}  # timestamp for session establish


class Session(object):

  """ Thin object representing a user session. Used at runtime until it needs
      to be stored, which then spawns a model instance (usually a
      ``ClientSession``). """

  __slots__ = ('__id__', '__session__')

  def __init__(self, key=None,
                     model=ClientSession,
                     **kwargs):

    """ Initialize this ``Session`` object with an ID and session model.

        :param key: ``str`` key to attach to the session model and pass back-
          and-forth as the user's session ID.

        :param model: Model class to use for spawning the new session and
          persisting it.

        :param **kwargs: Extra keyword arguments to pass to ``model``'s
          constructor. """

    if isinstance(model, type):
      # set established timestamp if it's not there already
      # (keep ``seen`` up to date too)
      if 'established' not in kwargs:
        kwargs['established'] = kwargs['seen'] = int(time.time())

      if 'data' not in kwargs: kwargs['data'] = {}

      for k, v in kwargs.iteritems():
        if k not in _BUILTIN_SESSION_PROPERTIES:
          kwargs['data'][k] = v

      # it's a class
      key = Session.make_key(key, model)
      self.__id__, self.__session__ = (key.id,
                                       model(key=key, **kwargs))

    elif not kwargs:
      # it's an instance, set the ID and session
      self.__session__, self.__id__ = model, id

    else:
      raise RuntimeError('Cannot specify a session model'
                         ' instance and also additional kwargs.')

  # noinspection PyMethodParameters
  @decorators.classproperty
  def config(cls):

    """  """

    # @TODO(sgammon): convert to decorator
    return config.Config().get('Sessions', {'debug': True})

  ## == Accessors == ##
  id = property(lambda self: self.__id__)
  data = property(lambda self: self.__session__.data)
  csrf = property(lambda self: self.__session__.csrf or (
    setattr(self.__session__, 'csrf', self.generate_token()) or (
      self.__session__.csrf)))

  ## == Get/Set == ##
  def set(self, key, value, exception=Exception):

    """  """

    try:
      return setattr(self.data, key, value) or self
    except KeyError:
      if exception is not Exception:
          raise exception('Could not write to'
                          ' session item "%s".' % key)

  def get(self, key, default=None, exception=Exception):

    """  """

    if key in self.data: return self.data[key]
    if default: return default
    if exception is not Exception: raise exception('Could not resolve session'
                                                   ' data item "%s".' % key)

  # item protocol
  __getitem__ = lambda self, key: (
    self.get(key, exception=KeyError))

  __setitem__ = lambda self, key, value: (
    self.set(key, value, exception=KeyError))

  def __contains__(self, key):

    """  """

    return key in self.__session__.data

  ## == Reset == ##
  def reset(self, save=False, adapter=None):

    """  """

    # tombstone and clear CSRF
    self.__session__.csrf, self.__session__.tombstoned = None, True
    if save: self.save(adapter)
    return

  def reset_csrf(self, save=False, adapter=None):

    """  """

    # clear the current CSRF
    self.__session__.csrf = None

    # generate a new one and return, possibly forcing a save
    new_csrf = self.csrf
    if save: self.save(adapter)
    return new_csrf

  ## == Save/Load == ##
  def save(self, environ, adapter=None):

    """  """

    if 'REMOTE_ADDR' in environ:
      self.__session__.client = environ.get('REMOTE_ADDR')

    if 'HTTP_USER_AGENT' in environ:
      self.__session__.agent = environ.get('HTTP_USER_AGENT')

    if self.config.get('storage', {}).get('enable'):
      return self.__session__.put(adapter=adapter)

  @classmethod
  def load(cls, id, model=ClientSession, strict=False, data=None):

    """  """

    # manufacture our own session, by loading the model
    #_session = model.get(Session.make_key(id, model))
    _session = None  # @TODO(sgammon): fix this
    if _session: return cls(id, _session)
    if strict: return False  # possibly fail stuff hardcore
    return cls(id, data=dict(data.iteritems()))  # otherwise make a new one

  ## == Session IDs == ##
  @staticmethod
  def generate_token(salt=''):

    """  """

    return Session.config.get('hash', hashlib.sha256)(
      salt + reduce(operator.add, (
        random.choice(string.printable) for x in xrange(32)))
    ).hexdigest()

  @staticmethod
  def make_key(id=None, model=ClientSession):

    """  """

    return models.Key(model, id or (
      Session.generate_token(Session.config.get('salt', ''))))


class SessionEngine(object):

  """  """

  ## == Internals == ##
  __label__, __metaclass__ = None, abc.ABCMeta
  __api__, __path__, __config__ = None, None, {}

  def __init__(self, name, config, api):

    """  """

    self.__path__, self.__config__, self.__api__ = name, config, api

  ## == Accessors == ##
  api = property(lambda self: self.__api__)
  config = property(lambda self: self.__config__.get(self.__path__))
  session_config = property(lambda self: self.__config__)

  @staticmethod
  def configure(name, **config):

    """  """

    def add_engine(klass):

      """  """

      klass.__label__ = name
      Sessions.add_engine(name, klass, **config)
      return klass

    return add_engine

  ## == Abstract Methods == ##
  @abc.abstractmethod
  def load(self, context):

    """  """

    raise NotImplementedError('Method `SessionEngine.load` is abstract.')

  @abc.abstractmethod
  def commit(self, context, session):

    """  """

    raise NotImplementedError('Method `SessionEngine.commit` is abstract.')


@decorators.bind('sessions')
class Sessions(logic.Logic):

  """  """

  ## == Internals == ##
  __salt__ = None  # the secret value to prepend to the cookie before hashing
  __secret__ = None  # the secret value to use in cookie checksumming
  __engines__ = {}  # mapping of names to engines that are supported
  __algorithm__ = None  # hash algorithm to share between engines

  @decorators.classproperty
  def config(cls):

    """  """

    return config.Config().get('Sessions', {'debug': True})

  @decorators.classproperty
  def salt(cls):

    """  """

    if not cls.__salt__:
      cls.__salt__ = cls.config.get('salt')
      if not cls.__salt__:
        cls.__salt__ = Session.generate_token()
    return cls.__salt__

  @decorators.classproperty
  def secret(cls):

    """  """

    if not cls.__secret__:
      cls.__secret__ = cls.config.get('secret')
      if not cls.__secret__:
        cls.__secret__ = (Session.generate_token() + Session.generate_token())
    return cls.__secret__

  @decorators.classproperty
  def engines(cls):

    """  """

    for engine in cls.__engines__.iteritems():
      yield engine

  @classmethod
  def add_engine(cls, name, engine, **config):

    """  """

    cls.__engines__[name] = (engine, config)
    return cls

  @classmethod
  def get_engine(cls, name=None, context=None):

    """  """

    _CONTEXT, _context_cfg = (
      (False, {}) if not context else (
        True, config.Config().get(context, {}).get('sessions', {})))

    # try looking in config if no engine is specified
    if not name: name = _context_cfg.get('engine', 'cookies')

    # look for an explicit engine by name if requested
    if name in cls.__engines__:

      _engine, _engine_config = cls.__engines__[name]

      # build config, allowing overrides
      _config = {}
      if _CONTEXT:
        _config.update(config.Config().get('Sessions', {}))
        _config.update(_context_cfg)
      _config.update(_engine_config)

      return _engine(name, _config, cls)
    raise RuntimeError('No such session runtime: "%s".' % name)

  ## == Injected Methods == ##
  @decorators.bind('reset')
  def reset(self, redirect=None, save=True, engine=None):

    """  """

    pass

  @decorators.bind('establish', wrap=hooks.HookResponder('match', context=(
    'environ', 'endpoint', 'arguments', 'request', 'http')))
  def establish(self, environ, endpoint, arguments, request, http):

    """  """

    if request.session:  # are sessions enabled?

      session, engine = request.session  # extract session + engine

      # engine is loaded, but no session
      if not session and self.config.get('always_establish', True):
        return request.set_session(Session(), engine)

  @decorators.bind('load', wrap=hooks.HookResponder(*(
    'request', 'message'), context=('request', 'http')))
  def load(self, request, http):

    """  """

    if http:  # HTTP sessions

      assert request, "must have a request to load a session"

      session_cfg = http.config.get('sessions', {'enable': False})
      if session_cfg.get('enable', True):

        # find us an engine, yo, and default to cookie-based sessions (safest)
        engine = self.get_engine(name=session_cfg.get('engine', 'cookies'),
                                 context='http')

        engine.load(request=request, http=http)

  @decorators.bind('commit', wrap=hooks.HookResponder('response', context=(
    'status', 'headers', 'request', 'http', 'response')))
  def commit(self, status, headers, request, http, response):

    """  """

    if response:  # we can only apply sessions to full responses
      if request.session:  # are sessions enabled?

        session, engine = request.session  # extract engine and session

        # defer to engine to commit
        engine.commit(request=request, response=response, session=session)

  @decorators.bind('save', wrap=hooks.HookResponder('complete', context=(
                                    'response', 'request', 'http', 'environ')))
  def save(self, response, request, http, environ):

    """  """

    if request.session and response:  # are sessions enabled?

      session, engine = request.session  # extract engine and session

      # @TODO(sgammon): support custom adapters here

      # save the session via backend, along with request context
      session.save(environ, adapter=None)
