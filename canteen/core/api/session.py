# -*- coding: utf-8 -*-

'''

  canteen: core session API
  ~~~~~~~~~~~~~~~~~~~~~~~~~

  exposes an API for creating and maintaining session state for
  both cyclical and realtime connection models.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''


# stdlib
import time, hashlib, base64
import random, string, operator, abc

# core & model APIs
from . import cache
from . import CoreAPI
from canteen import model as models

# canteen utils
from canteen.util import config
from canteen.util import decorators


class Session(object):

  '''  '''

  __session__ = None  # holds model instance for session

  class UserSession(models.Model):

    '''  '''

    seen = int  # when this session was last seen
    data = dict  # attached session state data
    csrf = basestring  # token for use in a CSRF
    hash = basestring  # hash of the user's session content (last seen)
    agent = basestring  # useragent string last seen from this session
    client = basestring  # IP address last seen from this session
    tombstoned = bool  # whether this session has been destroyed
    established = int  # timestamp for when this session was established

  def __init__(self, id=None, model=UserSession, **kwargs):

    '''  '''

    if isinstance(model, type):
      # set established timestamp if it's not there already (keep ``seen`` up to date too)
      if 'established' not in kwargs: kwargs['established'] = kwargs['seen'] = time.time()
      self.__session__ = model(key=self.make_key(id, model), **kwargs)  # it's a class

    elif not kwargs:
      self.__session__ = model  # it's an instance

    else:
      raise RuntimeError('Cannot specify a session model instance and also additional kwargs.')

  @property
  def config(self):

    '''  '''

    return config.Config().get('SessionAPI', {'debug': True})

  @property
  def data(self):

    '''  '''

    return self.__session__.data

  @property
  def csrf(self):

    '''  '''

    if not self.__session__.csrf:
      self.__session__.csrf = self.generate_token()  # generate CSRF
    return self.__session__.csrf

  ## == Get/Set == ##
  def set(self, key, value, exception=False):

    '''  '''

    try:
      self.data[key] = value
      return self
    except KeyError:
      if exception: raise exception('Could not write to session item "%s".' % key)

  def get(self, key, default=None, exception=False):

    '''  '''

    if key in self.data: return self.data
    if default: return default
    if exception: raise exception('Could not resolve session data item "%s".' % key)

  # attribute protocol
  __getattr__ = lambda self, key: self.get(key, exception=AttributeError)
  __setattr__ = lambda self, key, value: self.set(key, value, exception=AttributeError)

  # item protocol
  __getitem__ = lambda self, key: self.get(key, exception=KeyError)
  __setitem__ = lambda self, key, value: self.set(key, value, exception=KeyError)

  ## == Reset == ##
  def reset(save=False, adapter=None):

    '''  '''

    # tombstone and clear CSRF
    self.__session__.csrf = None
    self.__session__.tombstoned = True
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
  def save(self, adapter=None):

    '''  '''

    return self.__session__.put(adapter=adapter)

  @classmethod
  def load(cls, id, model=UserSession, strict=False):

    '''  '''

    # manufacture our own session, by loading the model
    _session = model.get(self.make_key(id, model))
    if _session:
      return cls(_session)
    if strict: return False  # possibly fail stuff hardcore
    return cls()  # otherwise make a new one

  ## == Session IDs == ##
  @staticmethod
  def encode_id(session_id):

    '''  '''

    return base64.b64encode(session_id)

  @staticmethod
  def generate_token(salt=''):

    '''  '''

    return self.config.get('hash', hashlib.sha256)(salt + reduce(operator.add, (random.choice(string.printable) for x in xrange(32)))).hexdigest()

  @staticmethod
  def make_key(id=None, model=UserSession):

    '''  '''

    return models.Key(model, self.encode_id(id or self.generate_token(self.config.get('salt', ''))))


class SessionEngine(object):

  '''  '''

  ## == Internals == ##
  __label__, __metaclass__ = None, abc.ABCMeta

  def __init__(self, config):

    '''  '''

    self.__config__ = config

  @property
  def config(self):

    '''  '''

    return self.__config__

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
  __engines__ = {}

  @decorators.classproperty
  def config(cls):

    '''  '''

    return config.Config().get('SessionAPI', {'debug': True})

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

    # try looking in config if no engine is specified
    if not name: name = cls.config.get('engine')

    # look for an explicit engine by name if requested
    if name in cls.__engines__:

      if context:
        # allow contextual config
        context = cls.config.get(context, {})
      else:
        context = {}

      # build config, allowing overrides
      _config = {}
      _config.update(context.get('sessions', {}).get(name, {}))
      _config.update(self.config.get('SessionAPI', {}).get(name, {}))
      _config.update(config)

      return cls.__engines__[name](_config)
    raise RuntimeError('No such session runtime: "%s".' % name)

  ## == Injected Methods == ##
  @decorators.bind('session.reset')
  def reset(self, redirect=None, save=True, engine=None):

    '''  '''

    pass

  @decorators.bind('session.save')
  def save(self, engine=None):

    '''  '''

    pass

  @decorators.bind('session.load')
  def load(self, id=None, environ=None, engine=None):

    '''  '''

    pass

  @decorators.bind('session.establish')
  def establish(self, id=None, environ=None, engine=None):

    '''  '''

    pass


__all__ = (
  'Session',
  'SessionEngine',
  'SessionAPI'
)
