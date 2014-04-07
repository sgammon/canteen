# -*- coding: utf-8 -*-

'''

  canteen: model
  ~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

__version__ = 'v3'

# stdlib
import abc
import inspect
import operator

# model components
from . import query
from . import adapter
from . import exceptions

# model adapters
from .adapter import abstract, concrete
from .adapter import KeyMixin, ModelMixin

# datastructures
from canteen.util.struct import _EMPTY


# Globals / Sentinels
_NDB = False  # `canteen.model` no longer supports NDB
_MULTITENANCY = False  # toggle multitenant key namespaces
_DEFAULT_KEY_SCHEMA = tuple(['id', 'kind', 'parent'])  # default key schema
_MULTITENANT_KEY_SCHEMA = tuple(['id', 'kind', 'parent', 'namespace', 'app'])


## == Metaclasses == ##

## MetaFactory
class MetaFactory(type):

  ''' Abstract parent for Model API primitive metaclasses,
    such as :py:class:`AbstractKey.__metaclass__` and
    :py:class:`AbstractModel.__metaclass__`.

    Enforces the metaclass chain and proper :py:mod:`abc`
    compliance.

    .. note :: Metaclass implementors of this class **must**
           implement :py:meth:`cls.initialize()`, or
           :py:class:`Model` construction will yield a
           :py:exc:`NotImplementedError`.
  '''

  class __metaclass__(abc.ABCMeta):

    ''' Embedded metaclass - enforces ABC compliance and
      properly formats :py:attr:`cls.__name__`. '''

    __owner__ = 'MetaFactory'

    def __new__(cls, name=None, bases=tuple(), properties={}):

      ''' Factory for metaclasses classes. Regular
        metaclass factory function.

        If the target class definition has the attribute
        :py:attr:`cls.__owner__`, it will be taken as the
        target class' internal ``__name__``. ``basestring``
        and classes are accepted (in which case the bound
        class' name is taken instead).

        :param name: String name for the metaclass class to factory.
        :param bases: Metaclass class inheritance path.
        :param properties: Property dictionary, as defined inline.
        :returns: Factoried :py:class:`MetaFactory.__metaclass__` descendent.

        .. note:: This class is *two* levels up in the meta chain.
              Please note this is an *embedded* metaclass used for
              *metaclass classes*.
      '''

      # alias embedded metaclasses to their `__owner__` (for __repr__), then pass up the chain
      name = cls.__name__ = cls.__owner__ if hasattr(cls, '__owner__') else name
      return super(cls, cls).__new__(cls, name, bases, properties)  # enforces metaclass

  ## = Internal Methods = ##
  def __new__(cls, name=None, bases=tuple(), properties={}):

    ''' Factory for concrete metaclasses. Enforces
      abstract-ness (prevents direct construction) and
      dispatches :py:meth:`cls.initialize()`.

      :param name: String name for the metaclass to factory.
      :param bases: Inheritance path for the new concrete metaclass.
      :param properties: Property dictionary, as defined inline.
      :returns: Factoried :py:class:`MetaFactory` descendent.
      :raises: :py:exc:`model.exceptions.AbstractConstructionFailure`
           upon concrete construction.
    '''

    # fail on construction - embedded metaclasses cannot be instantiated
    if not name: raise exceptions.AbstractConstructionFailure(cls.__name__)

    # pass up to `type`, which properly enforces metaclasses
    impl = cls.initialize(name, bases, properties)

    # if we're passed a tuple, we're being asked to super-instantiate
    if isinstance(impl, tuple):
      return super(MetaFactory, cls).__new__(cls, *impl)
    return impl

  ## = Exported Methods = ##
  @classmethod  # @TODO: clean up `resolve`
  def resolve(cls, name, bases, properties, default=True):

    ''' Resolve a suitable model adapter for a given Model adapter.

      :param name: Class name, as provided to :py:meth:`__new__`.
      :param bases: Inheritance path for the target :py:class:`Model`.
      :param properties: Class definition, as provided to :py:meth:`__new__`.
      :keyword default: Whether to allow use of the default adapter. Defaults to ``True``.
      :returns: A suitable :py:class:`model.adapter.ModelAdapter` subclass.
      :raises: :py:exc:`model.exceptions.NoSupportedAdapters` in the case that no
           supported (or valid) adapters could be found.
      :raises: :py:exc:`model.exceptions.InvalidExplicitAdapter` in the case of an
           unavilable, explicitly-requested adapter.
    '''

    if '__adapter__' not in properties:

      for i in bases:
        if hasattr(i, '__adapter__'):
          return i.__adapter__

      # grab each supported adapter
      _adapters = [option for option in concrete if option.is_supported()]

      # fail with no adapters...
      if not _adapters: raise exceptions.NoSupportedAdapters()

      # if we only have one adapter, the choice is easy...
      if not default:
        return _adapters[0].acquire(name, bases, properties), tuple()
      return _adapters[0].acquire(name, bases, properties)

    # an explicit adapter was requested via an `__adapter__` class property
    _spec = properties['__adapter__']
    if not isinstance(_spec, (list, tuple)):
      _spec = [_spec]

    for _spec_item in _spec:
      for _a in concrete:
        if _a is _spec_item or _a.__name__ == _spec_item:
          return _a.acquire(name, bases, properties)
        # fallback to next adapter
        continue  # pragma: no cover

    raise exceptions.InvalidExplicitAdapter(properties['__adapter__'])

  ## = Abstract Methods = ##
  @abc.abstractmethod
  def initialize(cls, name, bases, properties):

    ''' Initialize a subclass. Must be overridden by child metaclasses. '''

    # `MetaFactory.initialize` is abstract
    raise NotImplementedError()  # pragma: no cover


## == Abstract Classes == ##

## AbstractKey
class AbstractKey(object):

  ''' Abstract Key class. '''

  ## = Encapsulated Classes = ##

  ## AbstractKey.__metaclass__
  # Constructs Key classes for use in the AppTools model subsystem.
  class __metaclass__(MetaFactory):

    ''' Metaclass for model keys. '''

    __owner__ = 'Key'
    __schema__ = _DEFAULT_KEY_SCHEMA

    @classmethod
    def initialize(cls, name, bases, pmap):

      ''' Initialize a Key class. '''

      # resolve adapter
      _adapter = cls.resolve(name, bases, pmap)
      _module = pmap.get('__module__', 'apptools.model')

      if name == 'AbstractKey':  # <-- must be a string
        return name, bases, dict([('__adapter__', _adapter)] + pmap.items())

      key_class = [  # build initial key class structure
        ('__slots__', set()),  # seal object attributes
        ('__bases__', bases),  # define bases for class
        ('__name__', name),  # set class name internals
        ('__owner__', None),  # reference to current owner entity
        ('__adapter__', _adapter),  # resolve adapter for key
        ('__module__', _module),  # add class package
        ('__persisted__', False)]  # default to not persisted

      # resolve schema and add key format items, initted to None
      _schema = [('__%s__' % x, None) for x in pmap.get('__schema__', cls.__schema__)]

      # return an argset for `type`
      # @TODO: convert to a dict comprehension someday
      return name, bases, dict(_schema + key_class + pmap.items())

    def mro(cls):

      ''' Generate a fully-mixed MRO for `AbstractKey` subclasses. '''

      if cls.__name__ == 'AbstractKey':  # `AbstractKey` MRO
        return (cls, KeyMixin.compound, object)

      if cls.__name__ == 'Key':  # `Key` MRO
        return (cls, AbstractKey, KeyMixin.compound, object)

      # `Key`-subclass MRO, with support for diamond inheritance
      return tuple(filter(lambda x: x not in (Key, AbstractKey), [cls] + list(cls.__bases__)) +
             [Key, AbstractKey, KeyMixin.compound, object])

    def __repr__(cls):

      ''' String representation of a `Key` class. '''

      # dump key schema
      return '%s(%s)' % (cls.__name__, ', '.join((i for i in reversed(cls.__schema__))))

  def __new__(cls, *args, **kwargs):

    ''' Intercepts construction requests for abstract model classes. '''

    # prevent direct instantiation of `AbstractKey`
    if cls.__name__ == 'AbstractKey':
      raise exceptions.AbstractConstructionFailure('AbstractKey')

    return super(_key_parent(), cls).__new__(*args, **kwargs)  # pragma: no cover

  def __eq__(self, other):

    ''' Test whether two keys are functionally identical. '''

    if (not self and not other) or (self and other):
      if isinstance(other, self.__class__):  # class check
        if self.__schema__ <= other.__schema__:  # subset check
          if self.__schema__ >= other.__schema__:  # superset check
            if isinstance(other, self.__class__):  # type check
              # last resort: check each data property
              return all((i for i in map(lambda x: getattr(other, x) == getattr(self, x), self.__schema__)))
    # didn't pass one of our tests
    return False  # pragma: no cover

  def __repr__(self):

    ''' Generate a string representation of this Key. '''

    pairs = ('%s=%s' % (k, getattr(self, k)) for k in reversed(self.__schema__))
    return "%s(%s)" % (self.__class__.__name__, ', '.join(pairs))

  # util: alias `__repr__` to string magic methods
  __str__ = __unicode__ = __repr__

  # util: support for `__nonzero__` and aliased `__len__`
  __nonzero__ = lambda self: isinstance(self.__id__, (basestring, int))
  __len__ = lambda self: (int(self.__nonzero__()) if self.__parent__ is None else sum((1 for i in self.ancestry)))

  ## = Property Setters = ##
  def _set_internal(self, name, value):

    ''' Set an internal property on a `Key`. '''

    # fail if we're already persisted (unless we're updating the owner)
    if self.__persisted__ and name != 'owner':
      raise exceptions.PersistedKey(name)
    setattr(self, '__%s__' % name, value)
    return self

  ## = Property Getters = ##
  def _get_ancestry(self):

    ''' Retrieve this Key's ancestry path. '''

    if self.__parent__:  # if we have a parent, yield upward
      for i in self.__parent__.ancestry: yield i
    yield self  # yield self to end the chain, and stop iteration
    raise StopIteration()

  ## = Property Bindings  = ##
  id = property(lambda self: self.__id__,
          lambda self, id: self._set_internal('id', id))

  app = property(lambda self: self.__app__,
           lambda self, app: self._set_internal('app', app))

  kind = property(lambda self: self.__kind__,
          lambda self, kind: self._set_internal('kind', kind))

  parent = property(lambda self: self.__parent__,
            lambda self, p: self._set_internal('parent', p))

  owner = property(lambda self: self.__owner__, None)  # `owner` is read-only
  ancestry = property(_get_ancestry, None)  # `ancestry` is read-only

  namespace = property(lambda self: self.__namespace__ if _MULTITENANCY else None,  # ns = `None` when disabled
             lambda self, ns: self._set_internal('namespace', ns) if _MULTITENANCY else None)


## AbstractModel
class AbstractModel(object):

  ''' Abstract Model class. '''

  __slots__ = tuple()

  ## = Encapsulated Classes = ##

  ## AbstractModel.__metaclass__
  # Initializes class-level property descriptors and re-writes model internals.
  class __metaclass__(MetaFactory):

    ''' Metaclass for data models. '''

    __owner__ = 'Model'

    @staticmethod
    def _get_prop_filter(inverse=False):

      ''' Closure to build a small filter utility. '''

      def _filter_prop(bundle):

        ''' Decide whether a property is kept as a data value. '''

        key, value = bundle  # extract, this is dispatched from ``{}.items``
        if key.startswith('_'): return inverse
        if isinstance(value, classmethod): return inverse
        if inspect.isfunction(value) or inspect.ismethod(value): return inverse
        return (not inverse)

      return _filter_prop

    @classmethod
    def initialize(cls, name, bases, properties):

      ''' Initialize a Model class. '''

      property_map = {}
      _nondata_map = {}

      # core classes eval before being defined - must use string name :(
      if name not in frozenset(['AbstractModel', 'Model']):

        modelclass = {}

        # parse spec (`name=<basetype>` or `name=<basetype>,<options>`)
        # also, model properties that start with '_' are ignored
        for prop, spec in filter(cls._get_prop_filter(), properties.iteritems()):

          # build a descriptor object and data slot
          basetype, options = (spec, {}) if not isinstance(spec, tuple) else spec
          property_map[prop] = Property(prop, basetype, **options)

        # drop non-data-properties into our ``_nondata_map``
        for prop, value in filter(cls._get_prop_filter(inverse=True), properties.iteritems()):
          _nondata_map[prop] = value

        # merge and clone all basemodel properties, update dictionary with property map
        if len(bases) > 1 or bases[0] != Model:

          # build a full property map, after reducing parents left -> right
          property_map = dict([(key, value) for key, value in reduce(lambda left, right: left + right,
                    [[(prop, b.__dict__[prop].clone()) for prop in b.__lookup__]
                    for b in bases] + [property_map.items()])])

        prop_lookup = frozenset((k for k, v in property_map.iteritems()))  # freeze property lookup
        model_adapter = cls.resolve(name, bases, properties)  # resolve default adapter for model

        _model_internals = {  # build class layout, initialize core model class attributes.
          '__impl__': {},  # holds cached implementation classes generated from this model
          '__name__': name,  # map-in internal class name (should be == to Model kind)
          '__kind__': name,  # kindname defaults to model class name
          '__bases__': bases,  # stores a model class's bases, so proper MRO can work
          '__lookup__': prop_lookup,  # frozenset of allocated attributes, for quick lookup
          '__adapter__': model_adapter,  # resolves default adapter class for this key/model
          '__module__': properties.get('__module__'),  # add model's module location for future import
          '__slots__': tuple()}  # seal-off object attributes (but allow weakrefs and explicit flag)

        modelclass.update(property_map)  # update at class-level with descriptor map
        modelclass.update(_nondata_map)  # update at class-level with non data properties
        modelclass.update(_model_internals)  # lastly, apply model internals (should always override)

        impl = super(MetaFactory, cls).__new__(cls, name, bases, modelclass)  # inject our own property map
        return impl.__adapter__._register(impl)

      return name, bases, properties  # pass-through to `type`

    def mro(cls):

      ''' Generate a fully-mixed method resolution order for `AbstractModel` subclasses. '''

      if cls.__name__ != 'AbstractModel':  # must be a string, `AbstractModel` constructs here
        if cls.__name__ != 'Model':  # must be a string, same reason as above
          return tuple([cls] + [i for i in cls.__bases__ if i not in (Model, AbstractModel)] +
                 [Model, AbstractModel, ModelMixin.compound, object])  # full inheritance chain
        return (cls, AbstractModel, ModelMixin.compound, object)  # inheritance for `Key`
      return (cls, ModelMixin.compound, object)  # inheritance for `AbstractKey`

    # util: generate string representation of `Model` class, like "Model(<prop1>, <prop n...>)".
    __repr__ = lambda cls: '%s(%s)' % (cls.__name__, ', '.join((i for i in cls.__lookup__))
                 if (cls.__name__ not in ('Model', 'AbstractModel')) else "%s()" % cls.__name__)

    def __setattr__(cls, name, value, exception=exceptions.InvalidAttributeWrite):

      ''' Disallow property mutation before instantiation. '''

      if name in cls.__lookup__: raise exception('mutate', name, cls)  # cannot mutate data before instantiation
      if name.startswith('__'): return super(AbstractModel.__metaclass__, cls).__setattr__(name, value)
      raise exception('create', name, cls)  # cannot create new properties before instantiation

    def __getitem__(cls, name, exception=exceptions.InvalidItem):

      ''' Override itemgetter syntax to return property
        objects at the class level. '''

      if name not in cls.__lookup__: raise exception('read', name, cls)  # cannot read non-data properties
      return cls.__dict__[name]


  ## AbstractModel.PropertyValue
  # Small, ultra-lightweight datastructure responsible for holding a property value bundle for an entity attribute.
  class _PropertyValue(tuple):

    ''' Named-tuple class for property value bundles. '''

    __slots__ = tuple()
    __fields__ = ('dirty', 'data')

    def __new__(_cls, data, dirty=False):

      ''' Create a new `PropertyValue` instance. '''

      return tuple.__new__(_cls, (data, dirty))  # pass up-the-chain to `tuple`

    # util: generate a string representatin of this `_PropertyValue`
    __repr__ = lambda self: "Value(%s)%s" % (('"%s"' % self[0]) if isinstance(self[0], basestring)
                         else self[0].__repr__(), '*' if self[1] else '')

    # util: reduce arguments for pickle
    __getnewargs__ = lambda self: tuple(self)

    # util: lock down classdict
    __dict__ = property(lambda self: dict(zip(self.__fields__, self)))

    # util: map data and dirty properties
    data = property(operator.itemgetter(0), doc='Alias for `PropertyValue.data` at index 0.')
    dirty = property(operator.itemgetter(1), doc='Alias for `PropertyValue.dirty` at index 1.')

  # = Internal Methods = #
  def __new__(cls, *args, **kwargs):

    ''' Intercepts construction requests for directly Abstract model classes. '''

    if cls.__name__ == 'AbstractModel':  # prevent direct instantiation
      raise exceptions.AbstractConstructionFailure('AbstractModel')
    return super(AbstractModel, cls).__new__(cls, *args, **kwargs)

  # util: generate a string representation of this entity, alias to string conversion methods too
  __repr__ = __str__ = __unicode__ = lambda self: "%s(%s, %s)" % (self.__kind__, self.__key__,
                          ', '.join(['='.join([k, str(self.__data__.get(k, None))])
                                 for k in self.__lookup__]))

  def __setattr__(self, name, value, exception=exceptions.InvalidAttribute):

    ''' Attribute write override. '''

    # internal properties, data properties and `key` can be written to after construction
    if name.startswith('__') or name in self.__lookup__ or name == 'key':
      return super(AbstractModel, self).__setattr__(name, value)  # delegate upwards for write
    raise exception('set', name, self.kind())

  def __getitem__(self, name):

    ''' Item getter support. '''

    if name not in self.__lookup__:  # only data properties are exposed via `__getitem__`
      raise exceptions.InvalidItem('get', name, self.kind())
    return getattr(self, name)  # proxy to attribute API

  # util: support for python's item API
  __setitem__ = lambda self, item, value: self.__setattr__(item, value, exceptions.InvalidItem)

  def __context__(self, _type=None, value=None, traceback=None):

    ''' Context enter/exit - apply explicit mode. '''

    if traceback:  # pragma: no cover
      return False  # in the case of an exception in-context, bubble it up
    self.__explicit__ = (not self.__explicit__)  # toggle explicit status
    return self

  # util: alias context entry/exit to `__context__` toggle method
  __enter__ = __exit__ = __context__

  # util: proxy `len` to length of written data (also alias `__nonzero__`)
  __len__ = lambda self: len(self.__data__)
  __nonzero__ = __len__

  # util: `dirty` property flag, proxies to internal `_PropertyValue`(s) for dirtyness
  __dirty__ = property(lambda self: any((dirty for value, dirty in self.__data__.itervalues())))

  # util: `persisted` property flag, indicates whether internal key has been persisted in storage
  __persisted__ = property(lambda self: self.key.__persisted__)

  def __iter__(self):

    ''' Allow models to be used as dict-like generators. '''

    for name in self.__lookup__:
      value = self._get_value(name, default=Property._sentinel)

      # skip unset properties without a default, except in `explicit` mode
      if (value == Property._sentinel and (not self.__explicit__)):
        if self.__class__.__dict__[name]._default != Property._sentinel:
          yield name, self.__class__.__dict__[name]._default  # return a prop's default in `implicit` mode
        continue  # pragma: no cover
      yield name, value
    raise StopIteration()

  def _set_persisted(self, flag=False):

    ''' Notify this entity that it has been persisted to storage. '''

    self.key.__persisted__ = True
    for name in self.__data__:  # iterate over set properties
      # set value to previous, with `False` dirty flag
      self._set_value(name, self._get_value(name, default=Property._sentinel), False)
    return self

  def _get_value(self, name, default=None):

    ''' Retrieve the value of a named property on this Entity. '''

    if name:  # calling with no args gives all values in (name, value) form
      if name in self.__lookup__:
        value = self.__data__.get(name, Property._sentinel)
        if not value:
          if self.__explicit__ and value is Property._sentinel:
            return Property._sentinel  # return _EMPTY sentinel in explicit mode, if property is unset
          return default  # return default value passed in
        return value.data  # return property value
      raise exceptions.InvalidAttribute('get', name, self.kind())
    return [(i, getattr(self, i)) for i in self.__lookup__]

  def _set_value(self, name, value=_EMPTY, _dirty=True):

    ''' Set (or reset) the value of a named property on this Entity. '''

    if not name: return self  # empty strings or dicts or iterables return self

    if isinstance(name, (list, dict)):
      if isinstance(name, dict):
        name = name.items()  # convert dict to list of tuples
      # filter out flags from caller
      return [self._set_value(k, i, _dirty=_dirty) for k, i in name if k not in ('key', '_persisted')]

    if isinstance(name, tuple):  # pragma: no cover
      name, value = name  # allow a tuple of (name, value), for use in map/filter/etc

    if name == 'key':  # if it's a key, set through _set_key
      return self._set_key(value).owner  # returns `self` :)

    if name in self.__lookup__:  # check property lookup
      # if it's a valid property, create a namedtuple value placeholder
      self.__data__[name] = self.__class__._PropertyValue(value, _dirty)
      return self
    raise exceptions.InvalidAttribute('set', name, self.kind())

  def _set_key(self, value=None, **kwargs):

    ''' Set this Entity's key manually. '''

    # cannot provide both a value and formats
    if value and kwargs:
      raise exceptions.MultipleKeyValues(self.kind(), value, kwargs)

    # for a literal key value
    if value is not None:
      if not isinstance(value, (self.__class__.__keyclass__, tuple, basestring)):  # filter out invalid key types
        raise exceptions.InvalidKey(type(value), value, self.__class__.__keyclass__.__name__)

      self.__key__ = {  # set local key from result of dict->get(<formatter>)->__call__(<value>)

        self.__class__.__keyclass__: lambda x: x,  # return keys directly
        tuple: self.__class__.__keyclass__.from_raw,  # pass tuples through `from_raw`
        basestring: self.__class__.__keyclass__.from_urlsafe  # pass strings through `from_urlsafe`

      }.get(type(value), lambda x: x)(value)._set_internal('owner', self)  # resolve by value type and execute

      return self.__key__  # return key

    if kwargs:  # filter out multiple formats
      formatter, value = kwargs.items()[0]
      if len(kwargs) > 1:  # disallow multiple format kwargs
        raise exceptions.MultipleKeyFormats(', '.join(kwargs.keys()))

      self.__key__ = {  # resolve key converter, if any, set owner, and `__key__`, and return

        'raw': self.__class__.__keyclass__.from_raw,  # for raw, pass through `from_raw`
        'urlsafe': self.__class__.__keyclass__.from_urlsafe,  # for strings, pass through `from_urlsafe`
        'constructed': lambda x: x  # by default it's a constructed key

      }.get(formatter, lambda x: x)(value)._set_internal('owner', self)
      return self.__key__

    # except in the case of a null value and no formatter args (completely empty `_set_key`)
    raise exceptions.UndefinedKey(value, kwargs)  # fail if we don't have a key at all

  ## = Property Bindings  = ##
  key = property(lambda self: self.__key__, _set_key)  # bind model key


## == Concrete Classes == ##

## Key
class Key(AbstractKey):

  ''' Concrete Key class. '''

  __separator__ = u':'  # separator for joined/encoded keys
  __schema__ = _DEFAULT_KEY_SCHEMA if not _MULTITENANCY else _MULTITENANT_KEY_SCHEMA

  ## = Internal Methods = ##
  def __new__(cls, *parts, **formats):

    ''' Constructs keys from various formats. '''

    formatter, value = formats.items()[0] if formats else ('__constructed__', None)  # extract 1st-provided format

    if len(filter(lambda x: x[0] != '_persisted', formats.iteritems())) > 1:  # disallow multiple key formats
      raise exceptions.MultipleKeyFormats(', '.join(formats.keys()))

    return {  # delegate full-key decoding to classmethods
      'raw': cls.from_raw,
      'urlsafe': cls.from_urlsafe
    }.get(formatter, lambda x: super(AbstractKey, cls).__new__(cls, *parts, **formats))(value)

  def __init__(self, *parts, **kwargs):

    ''' Initialize this Key. '''

    if len(parts) > 1:  # normal case: it's a full/partially-spec'd key

      if len(parts) <= len(self.__schema__):  # it's a fully- or partially-spec'ed key
        mapped = zip([i for i in reversed(self.__schema__)][(len(self.__schema__) - len(parts)):],
               map(lambda x: x.kind() if hasattr(x, 'kind') else x, parts))

      else:
        # for some reason the schema falls short of our parts
        raise exceptions.KeySchemaMismatch(self.__class__.__name__, len(self.__schema__), str(self.__schema__))

      for name, value in map(lambda x: (x[0], x[1].kind()) if isinstance(x[1], Model) else x, mapped):
        setattr(self, name, value)  # set appropriate attribute via setter

    elif len(parts) == 1:  # special case: it's a kinded, empty key
      if hasattr(parts[0], 'kind'):
        parts = (parts[0].kind(),)  # quick ducktyping: is it a model? (`issubclass` only supports classes)
      self.__kind__ = parts[0]

    # if we *know* this is an existing key, `_persisted` should be `true`. also set kwarg-passed parent.
    self._set_internal('parent', kwargs.get('parent'))._set_internal('persisted', kwargs.get('_persisted', False))

  def __setattr__(cls, name, value):

    ''' Block attribute overwrites. '''

    if not name.startswith('__'):
      if name not in cls.__schema__:
        raise exceptions.InvalidKeyAttributeWrite('create', name, cls)
      if getattr(cls, name) is not None:
        raise exceptions.InvalidKeyAttributeWrite('overwrite', name, cls)
    return super(AbstractKey, cls).__setattr__(name, value)


## Property
class Property(object):

  ''' Concrete Property class. '''

  __metaclass__ = abc.ABCMeta  # enforce definition of `validate` for subclasses
  __slots__ = ('name', '_options', '_indexed', '_required', '_repeated', '_basetype', '_default')
  _sentinel = _EMPTY  # default sentinel for basetypes/values (read only, since it isn't specified in `__slots__`)

  ## = Internal Methods = ##
  def __init__(self, name, basetype, default=_sentinel, required=False, repeated=False, indexed=True, **options):

    ''' Initialize this Property. '''

    # copy locals specified above onto object properties of the same name, specified in `self.__slots__`
    map(lambda args: setattr(self, *args), zip(self.__slots__, (name, options, indexed,
                                  required, repeated, basetype, default)))

  ## = Descriptor Methods = ##
  def __get__(self, instance, owner):

    ''' Descriptor attribute access. '''

    if instance:  # proxy to internal entity method.

      # grab value, returning special a) property default or b) sentinel if we're in explicit mode and it is unset
      if self._default != Property._sentinel:  # we have a set default
        value = instance._get_value(self.name, default=self._default)
      else:
        value = instance._get_value(self.name, default=Property._sentinel)

      if not value and value == Property._sentinel and instance.__explicit__ is False:
        return None  # soak up sentinels via the descriptor API
      return value
    return self  # otherwise, class-level access is always the property in question

  def __set__(self, instance, value):

    ''' Descriptor attribute write. '''

    if instance is not None:  # only allow data writes after instantiation
      return instance._set_value(self.name, value)  # delegate to `AbstractModel._set_value`
    raise exceptions.InvalidAttributeWrite('set', self.name, self.kind)

  __delete__ = lambda self, instance: instance.__set__(instance, None)  # delegate to `__set__`

  def valid(self, instance):

    ''' Validate the value of this property, if any. '''

    if self.__class__ != Property and hasattr(self, 'validate'):  # pragma: no cover
      return self.validate(instance)  # check for subclass-defined validator to delegate validation to

    value = instance._get_value(self.name)  # retrieve value

    # check required-ness
    if (value in (None, self._sentinel)):
      if self._required: raise exceptions.PropertyRequired(self.name, instance.kind())
      if value is self._sentinel: return True  # empty value, non-required, all good :)

    if isinstance(value, (list, tuple, set, frozenset)):  # check multi-ness
      if not self._repeated: raise exceptions.PropertyNotRepeated(self.name, instance.kind())
    else:
      if self._repeated: raise exceptions.PropertyRepeated(self.name, instance.kind())
      value = (value,)  # make value iterable

    for v in value:  # check basetype

      # it validates if 1) the field is typeless, or 2) the value is `None` or an instance of it's type
      if self._basetype is None or ((v is not self._sentinel) and isinstance(v, (self._basetype, type(None)))):
        continue
      raise exceptions.InvalidPropertyValue(*(
        self.name, instance.kind(), type(v).__name__, self._basetype.__name__))
    return True  # validation passed! :)

  @classmethod
  def __repr__(self):

    ''' Generate a string representation
      of this :py:class:`Property`.

      :returns: Stringified, human-readable
      value describing this :py:class:`Property`. '''

    return "Property(%s, type=%s)" % (self.name, self._basetype)

  __str__ = __repr__

  # util method to clone `Property` objects
  clone = lambda self: self.__class__(self.name, self._basetype, self._default,
                    self._required, self._repeated, self._indexed, **self._options)

  ## == Query Overrides (Operators) == ##
  __sort__ = lambda self, other, direction: query.Sort(self, other, direction=(direction or query.Sort.ASCENDING))
  __filter__ = lambda self, other, operator: query.Filter(self, other, operator=(operator or query.Filter.EQUALS))


  ## == Sort Spawn == ##
  __pos__ = lambda self: self.__sort__(query.Sort.ASCENDING)  # `+` operator override
  __neg__ = lambda self: self.__sort__(query.Sort.DESCENDING)  # `-` operator override


  ## == Filter Spawn == ##
  __eq__ = lambda self, other: self.__filter__(other, query.Filter.EQUALS)  # `==` operator override
  __ne__ = lambda self, other: self.__filter__(other, query.Filter.NOT_EQUALS)  # `!=` operator override
  __gt__ = lambda self, other: self.__filter__(other, query.Filter.GREATER_THAN)  # `>` operator override
  __ge__ = lambda self, other: self.__filter__(other, query.Filter.GREATER_THAN_EQUAL_TO)  # `>=` operator override
  __lt__ = lambda self, other: self.__filter__(other, query.Filter.LESS_THAN)  # `<` operator override
  __le__ = lambda self, other: self.__filter__(other, query.Filter.LESS_THAN_EQUAL_TO)  # `<=` operator override


## Model
class Model(AbstractModel):

  ''' Concrete Model class. '''

  __keyclass__ = Key

  ## = Internal Methods = ##
  def __init__(self, **properties):

    ''' Initialize this Model. '''

    # grab key / persisted flag, if any, and set explicit flag to `False`
    self.__explicit__, self.__initialized__ = False, True

    # initialize key, internals, and map any kwargs into data
    self.key, self.__data__ = properties.get('key', False) or self.__keyclass__(self.kind(), _persisted=False), {}
    self._set_value(properties, _dirty=(not properties.get('_persisted', False)))

  ## = Class Methods = ##
  kind = classmethod(lambda cls: cls.__name__)


# Module Globals
__abstract__ = (abstract, MetaFactory, AbstractKey, AbstractModel)
__concrete__ = (concrete, Property, KeyMixin, ModelMixin, Key, Model)

# All modules
__all__ = (
  'concrete',
  'abstract',
  'MetaFactory',
  'AbstractKey',
  'AbstractModel',
  'query',
  'Property',
  'KeyMixin',
  'ModelMixin',
  'Key',
  'Model',
  'adapter',
  'exceptions'
)
