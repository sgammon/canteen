# -*- coding: utf-8 -*-

'''

  canteen: core session API
  ~~~~~~~~~~~~~~~~~~~~~~~~~

  exposes an API for creating and maintaining session state for
  both cyclical and realtime connection models.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''


# stdlib
import time, hashlib, base64
import random, string, operator, abc

# core & model APIs
from . import hooks, CoreAPI
from canteen import model as models

# canteen utils
from canteen.util import config
from canteen.util import decorators


class Session(object):

  '''  '''

  __id__ = None  # session ID slot
  __session__ = None  # holds model instance for session

  class UserSession(models.Model):

    '''  '''

    seen = int  # when this session was last seen
    data = dict  # attached session state data
    csrf = basestring  # token for use in a CSRF
    agent = basestring  # useragent string last seen from this session
    client = basestring  # IP address last seen from this session
    tombstoned = bool, {'default': False}  # whether this session has been destroyed
    established = int, {'required': True}  # timestamp for when this session was established

  def __init__(self, id=None, model=UserSession, **kwargs):

    '''  '''

    if isinstance(model, type):
      # set established timestamp if it's not there already (keep ``seen`` up to date too)
      if 'established' not in kwargs: kwargs['established'] = kwargs['seen'] = int(time.time())

      if 'data' not in kwargs: kwargs['data'] = {}

      for k, v in kwargs.iteritems():
        if k not in frozenset(('seen', 'data', 'csrf', 'established', 'seen', 'agent', 'client', 'tombstoned')):
          kwargs['data'][k] = v

      self.__session__ = model(key=Session.make_key(id, model), **kwargs)  # it's a class
      self.__id__ = self.__session__.key.id

    elif not kwargs:
      self.__session__, self.__id__ = model, id  # it's an instance, set the ID and session

    else:
      raise RuntimeError('Cannot specify a session model instance and also additional kwargs.')

  @decorators.classproperty
  def config(cls):

    '''  '''

    return config.Config().get('SessionAPI', {'debug': True})

  ## == Accessors == ##
  id = property(lambda self: self.__id__)
  data = property(lambda self: self.__session__.data)
  csrf = property(lambda self: self.__session__.csrf or (
    setattr(self.__session__, 'csrf', self.generate_token()) or self.__session__.csrf))

  ## == Get/Set == ##
  def set(self, key, value, exception=False):

    '''  '''

    try:
      return setattr(self.data, key, value) or self
    except KeyError:
      if exception: raise exception('Could not write to session item "%s".' % key)

  def get(self, key, default=None, exception=False):

    '''  '''

    if key in self.data: return self.data[key]
    if default: return default
    if exception: raise exception('Could not resolve session data item "%s".' % key)

  # item protocol
  __getitem__ = lambda self, key: self.get(key, exception=KeyError)
  __setitem__ = lambda self, key, value: self.set(key, value, exception=KeyError)

  def __contains__(self, key):

    '''  '''

    return key in self.__session__.data

  ## == Reset == ##
  def reset(save=False, adapter=None):

    '''  '''

    # tombstone and clear CSRF
    self.__session__.csrf, self.__session__.tombstoned = None, True
    if save: self.save(adapter)
    return

  def reset_csrf(save=False, adapter=None):

    '''  '''

    # clear the current CSRF
    self.__session__.csrf = None

    # generate a new one and return, possibly forcing a save
    new_csrf = self.csrf
    if save: self.save(adapter)
    return new_csrf

  ## == Save/Load == ##
  def save(self, environ, adapter=None):

    '''  '''

    if 'REMOTE_ADDR' in environ: self.__session__.client = environ.get('REMOTE_ADDR')
    if 'HTTP_USER_AGENT' in environ: self.__session__.agent = environ.get('HTTP_USER_AGENT')

    if self.config.get('storage', {}).get('enable'):
      return self.__session__.put(adapter=adapter)

  @classmethod
  def load(cls, id, model=UserSession, strict=False, data=None):

    '''  '''

    # manufacture our own session, by loading the model
    #_session = model.get(Session.make_key(id, model))
    _session = None  # @TODO(sgammon): fix this
    if _session: return cls(id, _session)
    if strict: return False  # possibly fail stuff hardcore
    return cls(id, data=dict(data.iteritems()))  # otherwise make a new one

  ## == Session IDs == ##
  @staticmethod
  def generate_token(salt=''):

    '''  '''

    return Session.config.get('hash', hashlib.sha256)(
      salt + reduce(operator.add, (random.choice(string.printable) for x in xrange(32)))
    ).hexdigest()

  @staticmethod
  def make_key(id=None, model=UserSession):

    '''  '''

    return models.Key(model, id or Session.generate_token(Session.config.get('salt', '')))


class SessionEngine(object):

  '''  '''

  ## == Internals == ##
  __label__, __metaclass__ = None, abc.ABCMeta
  __api__, __path__, __config__ = None, None, {}

  def __init__(self, name, config, api):

    '''  '''

    self.__path__, self.__config__, self.__api__ = name, config, api

  ## == Accessors == ##
  api = property(lambda self: self.__api__)
  config = property(lambda self: self.__config__.get(self.__path__))
  session_config = property(lambda self: self.__config__)

  @staticmethod
  def configure(name, **config):

    '''  '''

    def add_engine(klass):

      '''  '''

      klass.__label__ = name
      SessionAPI.add_engine(name, klass, **config)
      return klass

    return add_engine

  ## == Abstract Methods == ##
  @abc.abstractmethod
  def load(self, context):

    '''  '''

    raise NotImplementedError('Method `SessionEngine.load` is abstract.')

  @abc.abstractmethod
  def commit(self, context, session):

    '''  '''

    raise NotImplementedError('Method `SessionEngine.commit` is abstract.')


@decorators.bind('sessions')
class SessionAPI(CoreAPI):

  '''  '''

  ## == Internals == ##
  __salt__ = None  # the secret value to prepend to the cookie before hashing
  __secret__ = None  # the secret value to use in cookie checksumming
  __engines__ = {}  # mapping of names to engines that are supported
  __algorithm__ = None  # hash algorithm to share between engines

  @decorators.classproperty
  def config(cls):

    '''  '''

    return config.Config().get('SessionAPI', {'debug': True})

  @decorators.classproperty
  def salt(cls):

    '''  '''

    if not cls.__salt__:
      cls.__salt__ = cls.config.get('salt')
      if not cls.__salt__:
        cls.__salt__ = Session.generate_token()
    return cls.__salt__

  @decorators.classproperty
  def secret(cls):

    '''  '''

    if not cls.__secret__:
      cls.__secret__ = cls.config.get('secret')
      if not cls.__secret__:
        cls.__secret__ = (Session.generate_token() + Session.generate_token())
    return cls.__secret__

  @decorators.classproperty
  def engines(cls):

    '''  '''

    for engine in cls.__engines__.iteritems():
      yield engine

  @classmethod
  def add_engine(cls, name, engine, **config):

    '''  '''

    cls.__engines__[name] = (engine, config)
    return cls

  @classmethod
  def get_engine(cls, name=None, context=None):

    '''  '''

    _CONTEXT, _context_cfg = (
      (False, {}) if not context else (True, config.Config().get(context, {}).get('sessions', {}))
    )

    # try looking in config if no engine is specified
    if not name: name = _context_cfg.get('engine', 'cookies')

    # look for an explicit engine by name if requested
    if name in cls.__engines__:

      _engine, _engine_config = cls.__engines__[name]

      # build config, allowing overrides
      _config = {}
      if _CONTEXT:
        _config.update(config.Config().get('SessionAPI', {}))
        _config.update(_context_cfg)
      _config.update(_engine_config)

      return _engine(name, _config, cls)
    raise RuntimeError('No such session runtime: "%s".' % name)

  ## == Injected Methods == ##
  @decorators.bind('reset')
  def reset(self, redirect=None, save=True, engine=None):

    '''  '''

    pass

  @decorators.bind('establish', wrap=hooks.HookResponder('match', context=('environ', 'endpoint', 'arguments', 'request', 'http')))
  def establish(self, environ, endpoint, arguments, request, http):

    '''  '''

    if request.session:  # are sessions enabled?

      session, engine = request.session  # extract session + engine

      if not session and self.config.get('always_establish', True):  # engine is loaded, but no session
        return request.set_session(Session(), engine)

  @decorators.bind('load', wrap=hooks.HookResponder('request', 'message', context=('request', 'http')))
  def load(self, request, http):

    '''  '''

    if http:  # HTTP sessions

      assert request, "must have a request to load a session"

      session_cfg = http.config.get('sessions', {'enable': False})
      if session_cfg.get('enable', True):

        # find us an engine, yo
        engine = self.get_engine(name=session_cfg.get('engine', 'cookies'), context='http')  # default to cookie-based sessions (safest)
        engine.load(request=request, http=http)

  @decorators.bind('commit', wrap=hooks.HookResponder('response', context=('status', 'headers', 'request', 'http', 'response')))
  def commit(self, status, headers, request, http, response):

    '''  '''

    if response:  # we can only apply sessions to full responses
      if request.session:  # are sessions enabled?

        session, engine = request.session  # extract engine and session
        engine.commit(request=request, response=response, session=session)  # defer to engine to commit

  @decorators.bind('save', wrap=hooks.HookResponder('complete', context=('response', 'request', 'http', 'environ')))
  def save(self, response, request, http, environ):

    '''  '''

    if request.session and response:  # are sessions enabled?

      session, engine = request.session  # extract engine and session

      # @TODO(sgammon): support custom adapters here
      session.save(environ, adapter=None)  # save the session via backend, along with request context


__all__ = (
  'Session',
  'SessionEngine',
  'SessionAPI'
)
