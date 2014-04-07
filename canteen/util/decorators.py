# -*- coding: utf-8 -*-

'''

  canteen: decorator utils
  ~~~~~~~~~~~~~~~~~~~~~~~~

  useful (and sometimes critical) decorators, for use inside and
  outside :py:mod:`canteen`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

## ``classproperty`` - use like ``@property``, but at the class-level.
class classproperty(property):

  ''' Custom decorator for class-level property getters.
      Usable like ``@property`` and chainable with
      ``@memoize``, as long as ``@memoize`` is used as
      the inner decorator. '''

  def __get__(self, instance, owner):

    ''' Return the property value at the class level.

        :param instance: Current encapsulating object
        dispatching via the descriptor protocol,
        ``None`` if we are being dispatched from the
        class level.

        :param owner: Corresponding owner type, available
        whether we're dispatching at the class or instance
        level.

        :returns: Result of a ``classmethod``-wrapped,
        ``property``-decorated method. '''

    return classmethod(self.fget).__get__(None, owner)()


## ``memoize`` - cache the output of a property descriptor call
class memoize(property):

  ''' Custom decorator for property memoization. Usable
      like ``@property`` and chainable with ``@classproperty``,
      the utility decorator above. '''

  _value = None
  __initialized__ = False

  def __get__(self, instance, owner):

    ''' If we have a cached value attached to this
        context, return it.

        :param instance: Current encapsulating object
        dispatching via the descriptor protocol, or
        ``None`` if we are being dispatched from the
        class level.

        :param owner: Owner type for encapsulating
        object, if dispatched at the instance level.

        :raises: Re-raises all exceptions encountered
        in the case of an unexpected state during
        delegated property dispatch.

        :returns: Cached value, if any. If there is
        no cached value, defers to decorated method. '''

    if not self.__initialized__:
      if isinstance(self.fget, classproperty):
        self._value = classmethod(self.fget.fget).__get__(None, owner)()
      else:
        self._value = self.fget.__get__(instance, owner)()
      self.__initialized__ = True
    return self._value


## `` ``
class cached(object):

  '''  '''

  __func__ = None
  __cache__ = {}

  def __init__(self, callable):

    '''  '''

    self.__func__ = callable

  def wrap(self, instance):

    '''  '''

    def cache(*args, **kwargs):
      ps, kw = tuple(args), tuple(kwargs.items())
      if (ps, kw) not in self.__cache__:
        self.__cache__[(ps, kw)] = self.__func__(instance, *args, **kwargs)
      return self.__cache__[(ps, kw)]

    return cache

  def __get__(self, instance, owner):

    '''  '''

    return self.wrap(instance)


## ``configured`` - markup a class for use with canteen.
def configured(debug=False, path=None):

    ''' Prepare to inject config/path values
        at ``debug`` and ``path``.

        :param debug: Default value for class-level
        ``debug`` flag. Overridden in config. Defaults
        to ``False``.

        :param path: String path to configuration blob
        in main appconfig. Expected to be ``basestring``.
        Defaults to Python module/name classpath of
        injectee.

        :returns: Closure that constructs an injected
        target class. '''

    # resolve appconfig
    try:
        import config as appconfig
    except ImportError:
        class Config(object):
            debug = True
            config = {}
        appconfig = Config()

    # build injection closure
    def inject(klass):

        ''' Injection closure that prepares ``klass``
            with basic apptools structure.

            :param klass: Target class slated for injection.
            :returns: Injected class structure. '''

        def _config(cls):

            ''' Named config pipe. Resolves configuration
                at the local class' :py:attr:`cls._config_path`,
                if any, which is usually injected by apptools
                utils or provided manually.

                :returns: Configuration ``dict``, from main appconfig,
                or default ``dict`` of ``{'debug': True}``. '''

            #return appconfig.config.get(path or cls._config_path if hasattr(cls, '_config_path') else '.'.join((cls.__module__, cls.__name__)), {'debug': True})

        def _logging(cls):

            ''' Named logging pipe. Prepares custom Logbook/Python-backed
                ``Logger`` via config path and class name. Allows fine
                grained control of logging output, even at the individual
                class level.

                :returns: Customized :py:class:`debug.AppToolsLogger` class,
                attached with injectee's module path and name (or config
                path, if configured). '''

            #from apptools.util import debug

            # calculate configuration path
            #_config_path = path or cls._config_path if hasattr(cls, '_config_path') else '.'.join((cls.__module__, cls.__name__))
            #_csplit = _config_path.split('.')

            #return debug.AppToolsLogger(**{
            #    'path': '.'.join(_csplit[:-1]),
            #    'name': _csplit[-1]
            #})._setcondition(cls.config.get('debug', True))

        # attach injected properties and classmethods
        #klass._config_path = path or '.'.join((klass.__module__, klass.__name__))
        klass.config, klass.logging = memoize(classproperty(_config)), memoize(classproperty(_logging))
        return klass

    return inject


def singleton(target):

  '''  '''

  if isinstance(target, type):
    setattr(target, '__singleton__', True)  # indicate this is a singleton class
    return target
  else:
    raise RuntimeError('Only classes may be marked/decorated as singletons. Got: "%s".' % target)


## `` ``
class bind(object):

  '''  '''

  __alias__ = None  # injection alias (i.e. `source.<alias> == <target>`)
  __target__ = None  # target for injection - i.e. what should be injected
  __config__ = None  # optional *args and **kwargs to wrap ``config`` (above)
  __namespace__ = True  # do we namespace this property under it's superbind? (methods only)

  def __init__(self, alias=None, namespace=True, *args, **kwargs):

    '''  '''

    self.__alias__, self.__config__, self.__namespace__ = (
      alias,
      (args, kwargs) if (args or kwargs) else None,
      namespace  # wrap `decorators.config` (optional)
    )

  def __repr__(self):

    '''  '''

    return "<binding '%s'>" % self.__alias__ or self.__target__.__name__

  def __call__(self, target):

    '''  '''

    from ..core import meta  # no deps in util. ever. :)

    # default to binding name
    self.__alias__ = self.__alias__ or target.__name__

    # install aliases
    target.__binding__, target.__target__, self.__target__ = self, self.__alias__, target

    # are we decorating a class?
    if isinstance(target, type):

      if issubclass(target.__class__, meta.Proxy.Registry):

        _bindings, _aliases, _hooks = set(), {}, []

        # prepare singleton if requested
        if hasattr(target, '__singleton__') and target.__singleton__:
          target.__class__.prepare(target)

        # scan for "bound" methods (bound for DI, not for Python)
        for mapping in (target.__dict__, target.__class__.__dict__):

          for k, v in mapping.iteritems():

            if k.startswith('__'): continue

            # is this a wrapped method? unwrap it
            if isinstance(v, (staticmethod, classmethod)):
              v = v.__func__  # unwrap from wrapped class/static decorator

            # is this a bound (i.e. dependency-injected) method?
            if hasattr(v, '__binding__') and v.__binding__:
              _bindings.add(k)
              if v.__binding__.__alias__:
                _aliases[v.__binding__.__alias__] = k

            # is this a hook method? register with self
            if hasattr(v, '__hooks__') and v.__hooks__:
              v.__register__(target)

        # attach bindings to target class
        target.__aliases__, target.__bindings__ = _aliases, frozenset(_bindings) if _bindings else None

        # bind locally, and internally
        return config(target, *self.__config__[0], **self.__config__[1]) if self.__config__ else target

      # only registry-enabled class trees can use ``bind``
      raise TypeError('Only meta-implementors of `meta.Proxy.Registry`'
                      ' (anything meta-deriving from `Registry` or `Component`'
                      ' can be bound to injection names.')

    # allow wrapping of hook responders
    from ..core import hooks
    if self.__config__ and self.__config__[1] and isinstance(self.__config__[1]['wrap'], hooks.HookResponder):
      self.__config__[1]['wrap'].__binding__ = self

    # are we decorating a method?
    return self.__config__[1]['wrap'](target) if (self.__config__ and 'wrap' in self.__config__[1]) else target


## `` ``
def cacheable(key, ttl=None, expire=None, passthrough=__debug__):

  '''  '''

  from canteen.core.api import cache

  # process expiration
  if ttl and expire:
    raise RuntimeError('Cannot provide both a TTL and absolute expiration for cacheable item "%s".' % key)

  elif ttl and isinstance(ttl, int):
    expiration = time.time() + ttl

  elif expire and isinstance(expire, int):
    expiration = expire  # integer absolute expiration

  elif expire and isinstance(expire, datetime.datetime):
    expiration = time.mktime(expire.timetuple())

  elif (not ttl) and (not expire):
    expiration = None

  else:
    raise RuntimeError('Invalid TTL or Expire value given for cacheable item "%s".' % key)

  # make our injector and responder
  def injector(func):

    '''  '''

    def responder(*args, **kwargs):

      '''  '''

      if passthrough:  # optionally passthrough and don't check cache
        return func(*args, **kwargs)

      # check expiration - flush if we have to
      if expiration and not (time.time() < expiration):

        print "Cache item expired: '%s'." % key

        cache.CacheAPI.delete(key)
        val = None
      else:
        val = cache.CacheAPI.get(key)

      # refresh the cache if we have to
      if not val:

        print "Cache miss: '%s'." % key

        val = func(*args, **kwargs)

        if val:
          cache.CacheAPI.set(key, val)

      else:
        print "Cache hit: '%s'." % key

      return val

    return responder

  return injector


__all__ = (
  'classproperty',
  'memoize',
  'cached',
  'configured',
  'bind',
  'cacheable',
  'singleton'
)
