# -*- coding: utf-8 -*-

'''

  model
  ~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

__version__ = 'v5'

# stdlib
import abc
import inspect
import operator

# model components
from . import query
from . import exceptions

# model adapters
from .adapter import abstract, concrete
from .adapter import KeyMixin, ModelMixin
from .adapter import VertexMixin, EdgeMixin

# datastructures
from canteen.util.struct import _EMPTY


# Globals / Sentinels
_NDB = False  # `canteen.model` no longer supports NDB
_MULTITENANCY = False  # toggle multitenant key namespaces
Edge = Vertex = Model = AbstractModel = None  # must initially be `None`
_DEFAULT_KEY_SCHEMA = ('id', 'kind', 'parent')  # default key schema
_MULTITENANT_KEY_SCHEMA = ('id', 'kind', 'parent', 'namespace', 'app')
_BASE_MODEL_CLS = frozenset(('Model', 'AbstractModel', 'Vertex', 'Edge'))
_BASE_GRAPH_CLS = frozenset(('Vertex', 'Edge'))
_PROPERTY_SLOTS = (
  'name',  # property string name (used as attribute/item key)
  '_options',  # arbitrary userland property options
  '_indexed',  # should this property be indexed?
  '_required',  # should property should be required?
  '_repeated',  # should property be allowed to keep multiple values?
  '_basetype',  # property basetype, for validation and storage
  '_default'  # default value for property, defaults to ``None``
)


def noglobal(name):

  ''' Simple utility to interrogate the global context
      and see if something is defined yet.

      :param name: Name to check for global definition
        in this module.

      :returns: Whether the target ``Name`` is defined
        in module globals and is not falsy. '''

  gl = globals()
  return (name in gl and (not gl[name]))


## == Metaclasses == ##

class MetaFactory(type):

  ''' Abstract parent for Model API primitive metaclasses,
      such as :py:class:`AbstractKey.__metaclass__` and
      :py:class:`AbstractModel.__metaclass__`.

      Enforces the metaclass chain and proper :py:mod:`abc`
      compliance.

      .. note :: Metaclass implementors of this class **must**
             implement :py:meth:`cls.initialize()`, or
             :py:class:`Model` construction will yield a
             :py:exc:`NotImplementedError`. '''

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
                *metaclass classes*. '''

      # alias embedded metaclasses to their `__owner__` (for __repr__)
      name = cls.__name__ = cls.__owner__ if hasattr(cls, '__owner__') else name

      # enforces metaclass
      return super(cls, cls).__new__(cls, name, bases, properties)

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
          upon concrete construction. '''

    # fail on construction - embedded metaclasses cannot be instantiated
    if not name: raise exceptions.AbstractConstructionFailure(cls.__name__)

    # pass up to `type`, which properly enforces metaclasses
    impl = cls.initialize(name, bases, properties)

    # if we're passed a tuple, we're being asked to super-instantiate
    if isinstance(impl, tuple):
      return super(MetaFactory, cls).__new__(cls, *impl)
    return impl

  ## = Exported Methods = ##
  @classmethod
  def resolve(cls, name, bases, properties, default=True):

    ''' Resolve a suitable model adapter for a given model Key or Model.

        :param name: Class name, as provided to :py:meth:`__new__`.
        :param bases: Inheritance path for the target :py:class:`Model`.
        :param properties: Class definition, as provided to :py:meth:`__new__`.
        :keyword default: Allow use of the default adapter. Defaults to `True`.
        :returns: A suitable :py:class:`model.adapter.ModelAdapter` subclass.

        :raises NoSupportedAdapters: in the case that no supported (or valid)
          adapters could be found.

        :raises InvalidExplicitAdapter: in the case of an unavailable,
          explicitly-requested adapter. '''

    from canteen.model.adapter import abstract

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

      if isinstance(_spec_item, (type, basestring)):
        for _a in concrete:
          if _a is _spec_item or _a.__name__ == _spec_item:
            return _a.acquire(name, bases, properties)

      elif issubclass(_spec_item.__class__, abstract.ModelAdapter):
        # it's a valid model adapter instance already
        return _spec_item  # pragma: no cover

    adapter_label = _spec
    if not isinstance(_spec, basestring):  # pragma: no cover
      if isinstance(_spec, type):
        adapter_label = _spec.__name__
      if issubclass(_spec.__class__, abstract.ModelAdapter):
        adapter_label = _spec.__class__.__name__
    raise exceptions.InvalidExplicitAdapter(adapter_label)

  ## = Abstract Methods = ##
  @abc.abstractmethod
  def initialize(cls, name, bases, properties):  # pragma: no cover

    ''' Initialize a subclass. Must be overridden by child metaclasses.

        :param name: Target class name to initialize.
        :param bases: Target class bases to mix in.
        :param properties: Bound properties to target class.

        :raises NotImplementedError: Always, if called directly, as this
          method is abstract. '''

    raise NotImplementedError()  # `MetaFactory.initialize` is abstract


## == Abstract Classes == ##

class AbstractKey(object):

  ''' Abstract Key class. Provides base abstract
      functionality supporting concrete Key objects. '''

  ## = Encapsulated Classes = ##
  class __metaclass__(MetaFactory):

    ''' Metaclass for model keys. Reorganizes internal
        class structure to support object-specific
        behavior. See ``cls.initialize`` for details. '''

    __owner__, __schema__ = 'Key', _DEFAULT_KEY_SCHEMA

    @classmethod
    def initialize(cls, name, bases, pmap):

      ''' Initialize a Key class. Reorganize class layout
          to support ``Key`` operations. The class property
          ``__schema__`` (expected to be an iterable of string
          schema item names) is scanned for key structure.

          The following non-standard class-level properties are set:
            - ``__slots__`` - frozen to nothing as everything is class-level
            - ``__owner__`` - owner model object for a key, if any
            - ``__adapter__`` - adapter for this key, resolved at class time
            - ``__persisted__`` - whether this key is known to be persisted

          Each schema'd key chunk is also given an internal-style
          property (read: surrounded by ``__``).

          :param name: Name of ``Key`` class to initialize.
          :param bases: Base classes to mix into target ``Key`` class.
          :param pmap: Map of properties bound to target ``Key`` class.

          :returns: Constructed type extending ``Key``. '''

      # resolve adapter
      _adapter = cls.resolve(name, bases, pmap)
      _module = pmap.get('__module__', 'canteen.model')

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
      _schema = [
        ('__%s__' % x, None) for x in pmap.get('__schema__', cls.__schema__)]

      # return an argset for `type`
      return name, bases, dict(_schema + key_class + pmap.items())

    def mro(cls):

      ''' Generate a fully-mixed MRO for `AbstractKey` subclasses.
          Handles injection of ``CompoundKey`` object in MRO to support
          ``KeyMixin`` composure.

          The non-base MRO pattern is as follows:
            - for ``AbstractKey``: ``KeyMixin -> object``
            - for ``Key``: `AbstractKey -> KeyMixin -> object``
            - for ``Key`` classes: ``Key -> AbstractKey -> KeyMixin -> object``

          :returns: Properly-mixed MRO for an `AbstractKey` subclass. '''

      if cls.__name__ == 'AbstractKey':  # `AbstractKey` MRO
        return (cls, KeyMixin.compound, object)

      if cls.__name__ == 'Key':  # `Key` MRO
        return (cls, AbstractKey, KeyMixin.compound, object)

      # `Key`-subclass MRO, with support for diamond inheritance
      return tuple(filter(lambda x: x not in (Key, AbstractKey), [cls] + (
        list(cls.__bases__))) + [Key, AbstractKey, KeyMixin.compound, object])

    def __repr__(cls):

      ''' String representation of a `Key` class. Note that this
          ``__repr__`` handles ``cls`` representation.

          :returns: ``x(y)`` where ``x`` is the `Key` class in use
            and ``y`` is collapsed key schema. '''

      # dump key schema
      return '%s(%s)' % (
        cls.__name__, ', '.join((i for i in reversed(cls.__schema__))))

  def __new__(cls, *args, **kwargs):

    ''' Intercepts construction requests for abstract model classes.
        Enforces abstractness, but otherwise passes calls to ``super``.

        :raises AbstractConstructionFailure: In the case that an attempt
          is made to construct an ``AbstractKey`` directly.

        :returns: New instance of `cls`, so long as `cls` it is concrete. '''

    # prevent direct instantiation of `AbstractKey`
    if cls.__name__ == 'AbstractKey':
      raise exceptions.AbstractConstructionFailure('AbstractKey')

    return super(cls, cls).__new__(*args, **kwargs)

  def __eq__(self, other):

    ''' Test whether two keys are functionally identical.

        Tries the following tests to negate equality:
        - target vs self falsyness
        - target vs self schema
        - target vs self type
        - target vs self data

        If all elements are reported to be equal, the keys
        are functionally identical. If any of the tests
        fail, the keys are not identical.

        :param other: Other key to test against ``self``.

        :returns: ``True`` if ``other`` is functionally
          identical to ``self``, otherwise ``False``. '''

    if (not self and not other) or (self and other):
      if isinstance(other, self.__class__):  # class check
        if self.__schema__ <= other.__schema__:  # subset check
          if self.__schema__ >= other.__schema__:  # superset check
            if isinstance(other, self.__class__):  # type check
              # last resort: check each data property
              return all((i for i in map(lambda x: (
                getattr(other, x) == getattr(self, x)), self.__schema__)))
    return False  # didn't pass one of our tests

  def __repr__(self):

    ''' Generate a string representation of this Key object.
        Note that this method is responsible for ``self``
        representation, not ``cls``.

        :returns: String describing the local ``Key`` object,
          like ``x(y)``, where ``x`` is the local ``Key``
          class name and ``y`` is a formatted list of this
          keys's schema and data. '''

    pairs = ('%s=%s' % (k, getattr(self, k)) for k in reversed(self.__schema__))
    return "%s(%s)" % (self.__class__.__name__, ', '.join(pairs))

  # util: alias `__repr__` to string magic methods
  __str__ = __unicode__ = __repr__

  # util: support for `__nonzero__` and aliased `__len__`
  __nonzero__ = lambda self: isinstance(self.__id__, (basestring, int))
  __len__ = lambda self: (
    int(self.__nonzero__()) if self.__parent__ is None else (
      sum((1 for i in self.ancestry))))

  ## = Property Setters = ##
  def _set_internal(self, name, value):

    ''' Set an internal property on a `Key`. Used by ``Key``
        internals to proxy attribute and item calls.

        :param name: Name of the internal property to set.
        :param value: Value to set the internal property to.

        :raises PersistedKey: If an internal property set is
          attempted on an already-persisted ``Key``.

        :returns: ``self``, for chainability. '''

    # fail if we're already persisted (unless we're updating the owner)
    if self.__persisted__ and name != 'owner':
      raise exceptions.PersistedKey(name)
    if name == 'parent' and isinstance(value, Model):
      value = value.key
    setattr(self, '__%s__' % name, value)
    return self

  ## = Property Getters = ##
  def _get_ancestry(self):

    ''' Retrieve this ``Key``'s ancestry path, one item at a
        time, starting from this ``Key``'s root and proceeding
        down the chain. Acts as a generator.

        :raises StopIteration: When no more ancestry entries
          are available to yield.

        :returns: Yields ancestry items one at a time, starting
          with this ``Key``'s root, and ending with ``self``. '''

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

  # ns = `None` when disabled
  namespace = property(lambda self: self.__namespace__ or None,
                       lambda self, ns: self._set_internal('namespace', ns))


## AbstractModel
class AbstractModel(object):

  ''' Abstract Model class. Specifies abstract
      properties that apply to all `Model`-style
      data containers.

      Applies an embedded `MetaFactory`-compliant
      metaclass to properly initialize subclasses. '''

  __slots__ = tuple()


  ## = Encapsulated Classes = ##
  class __metaclass__(MetaFactory):

    ''' Embedded `MetaFactory`-compliant metaclass.
        Handles initialization of new `AbstractModel`
        descendent classes.

        Reorganizes class layout and structure to
        satisfy future internal model operations.
        See ``cls.initialize`` for details. '''

    __owner__ = 'Model'

    @staticmethod
    def _get_prop_filter(inverse=False):

      ''' Builds a callable that can filter properties
          between internal and user-defined ones. Returns

          By default, the callable produced by this
          method will produce ``False`` if the property
          is internal and ``True`` otherwise.

          To flip this functionality, pass ``True`` to
          inverse, which simply converts the boolean
          response to ``True`` for internal properties,
          and ``False`` for user data.

          :param inverse: Flip the filter to only return
            truthy for internal properties. Defaults to
            ``False`` for internal-filter behavior.

          :returns: Closure that is appropriate for use
            with ``filter`` and returns ``True`` if the
            property ``bundle`` handed in is internal. '''

      def _filter_prop(bundle):

        ''' Decide whether a property is kept as a data
            value or a class internal. See wrapping
            function for full description.

            :param bundle: Property bundle to examine.

            :returns: ``True`` or ``False`` according
              to the property ``bundle``'s status as
              an internal property. '''

        key, value = bundle  # extract, this is dispatched from ``{}.items``
        if key.startswith('_'): return inverse
        if isinstance(value, classmethod): return inverse
        if inspect.isfunction(value) or inspect.ismethod(value): return inverse
        return (not inverse)

      return _filter_prop

    @classmethod
    def initialize(cls, name, bases, properties):

      ''' Initialize a ``Model`` descendent for use as a
          data model class. Reorganizes class internals
          to store descriptors for defined user data
          properties.

          Also injects a few properties into the class
          map to satisfy ``Model`` layer functionality.

          :param name: Name of the ``Model``-descendent
            class to initialize.

          :param bases: Base classes to extend with ``cls``
            target. Must include ``Model``, ``Vertex``,
            ``Edge`` or a class that extends one thereof.

          :param properties: Class property map, as defined
            inline or via a manual call to ``initialize``.
            Always expected to be a ``dict``.

          :raises AssertionError: If incorrect types are
            passed for ``name``, ``bases`` or ``properties``.
            ``__debug__`` must be active to enable assertions.

          :returns: Initialized target ``Model``-descendent
            class, with rewritten property map. '''

      assert isinstance(name, basestring), "class name must be a string"
      assert isinstance(bases, tuple), "class bases must be a tuple of types"
      assert isinstance(properties, dict), "class map must be a valid dict"

      property_map = {}
      _nondata_map = {}

      # core classes eval before being defined - must use string name :(
      if name not in frozenset(['AbstractModel', 'Model']):

        modelclass = {}

        # parse spec (`name=<basetype>` or `name=<basetype>,<options>`)
        # also, model properties that start with '_' are ignored
        for prop, spec in filter(cls._get_prop_filter(),
                                  properties.iteritems()):

          # build a descriptor object and data slot
          basetype, options = (
            (spec, {}) if not isinstance(spec, tuple) else spec)
          property_map[prop] = Property(prop, basetype, **options)

        # drop non-data-properties into our ``_nondata_map``
        for prop, value in filter(cls._get_prop_filter(inverse=True),
                                  properties.iteritems()):
          _nondata_map[prop] = value

        # merge and clone all basemodel properties, update dictionary
        if len(bases) > 1 or bases[0] is not Model:

          # build a full property map, after reducing parents left -> right
          _pmap_data = ([(
            [(prop, b.__dict__[prop].clone()) for prop in b.__lookup__])
              for b in bases] + [property_map.items()])

          # calculate full dict property map
          property_map = dict([(key, value) for key, value in (
            reduce(operator.add, _pmap_data))])

        # freeze property lookup
        prop_lookup = frozenset((k for k, v in property_map.iteritems()))

        # resolve default adapter for model
        model_adapter = cls.resolve(name, bases, properties)

        _model_internals = {  # build class layout, initialize core model
          '__impl__': {},  # holds cached implementation classes
          '__name__': name,  # add internal class name (should be Model kind)
          '__kind__': name,  # kindname defaults to model class name
          '__bases__': bases,  # stores a model class's bases, so MRO can work
          '__lookup__': prop_lookup,  # frozenset of allocated attributes
          '__adapter__': model_adapter,  # resolves default adapter class
          '__module__': properties.get('__module__'),  # add model's module
          '__slots__': tuple()}  # seal-off object attributes

        modelclass.update(property_map)  # update at class-level
        modelclass.update(_nondata_map)  # update at class-level with non data
        modelclass.update(_model_internals)  # lastly, apply model internals

        # for top-level graph objects
        if name in ('Edge', 'Vertex'):
          if noglobal(name):
            # make flag for edge/vertex class
            graph_object_flag = '__%s__' % name.lower()

            # mark as graph model and according type
            properties['__graph__'] = properties[graph_object_flag] = True

        # for graph-object subclasses
        elif any((hasattr(b, '__graph__') for b in bases)) or (
                name in ('Edge', 'Vertex')):

          # find owner name
          object_owner = 'Vertex' if (
            any((hasattr(b, '__vertex__') for b in bases))) else 'Edge'

          # set flags
          graph_flag = '__%s__' % object_owner.lower()
          _model_internals['__owner__'] = object_owner
          _model_internals['__graph__'] = _model_internals[graph_flag] = True

        # inject our own property map
        impl = super(MetaFactory, cls).__new__(cls, name, bases, modelclass)
        return impl.__adapter__._register(impl)

      return name, bases, properties  # pass-through to `type`

    def mro(cls):

      ''' Generate a fully-mixed method resolution order for
          `AbstractModel` subclasses.

          According to the parent base that we're extending,
          models get custom MRO chains to fulfill mixin
          attributes in the same Canteen-style DI at runtime.

          :raises RuntimeError: If MRO cannot be calculated
            because the target ``cls`` is completely invalid.

          :returns: Mixed MRO according to base class structure. '''

      def find_nonbase_mro():

        ''' Finds proper MRO for non-base classes, i.e. classes
            that actually make use of ``Model``, ``Edge`` or
            ``Vertex`` (not those classes themselves).

            :returns: Class-tree-specific MRO, if possible, in a
              ``list`` suitable for composure into a final MRO. '''

        base_models = frozenset((Vertex, Edge, Model, AbstractModel))

        # graph models?
        if any((hasattr(b, '__graph__') for b in cls.__bases__)):
          _vertex = any((hasattr(b, '__vertex__') for b in cls.__bases__))
          return [i for i in cls.__bases__ if i not in base_models] + [
                   Vertex if _vertex else Edge,
                   Model, AbstractModel,
                   VertexMixin.compound if _vertex else EdgeMixin.compound,
                   ModelMixin.compound]

        # vanilla non-base MRO
        return [i for i in cls.__bases__ if i not in base_models] + [
                  Model, AbstractModel, ModelMixin.compound]

      # calculate common `Model` MRO
      base_model_mro = (
        [ModelMixin.compound] if cls.__name__ == 'AbstractModel' else [
          AbstractModel, ModelMixin.compound])

      target_mro = {

        # `AbstractModel` just gets the mixin
        'AbstractModel': lambda: [ModelMixin.compound],

        # `Model` gets `AbstractModel` and mixin
        'Model': lambda: base_model_mro,

        # `Vertex` structure overrides `Model` structure
        'Vertex': lambda: [VertexMixin.compound, Model] + base_model_mro,

        # `Edge` structure overrides `Model` structure
        'Edge': lambda: [EdgeMixin.compound, Model] + base_model_mro,

      }.get(cls.__name__, find_nonbase_mro)()

      if not target_mro or not isinstance(target_mro, list):
        # not a base class
        raise RuntimeError('Unable to calculate MRO for unidentified'
                           ' MetaFactory-descendent Model class: %s.' % cls)

      return tuple([cls] + target_mro + [object])

    def __repr__(cls):

      ''' Generate string representation of `Model` class,
          like "Model(<prop1>, <prop n...>)".

          :returns: String representation of this `Model. '''

      if hasattr(cls, '__lookup__') and cls.__name__ not in _BASE_MODEL_CLS:
        return '%s(%s)' % (cls.__name__, ', '.join((i for i in cls.__lookup__)))

      elif (cls.__name__ in _BASE_GRAPH_CLS and cls.__owner__ == 'Model') or (
        cls.__name__ == 'Model' or cls.__name__ == 'AbstractModel'):
        return cls.__name__

      elif any((hasattr(b, '__graph__') for b in cls.__bases__)):
        _vertex = any((hasattr(b, '__vertex__') for b in cls.__bases__))
        return ("Vertex<%s>" if _vertex else "Edge<%s>") % cls.__name__

      return 'Model<%s>' % cls.__name__

    __str__ = __unicode__ = __repr__

    def __setattr__(cls, name, value,
                               exception=exceptions.InvalidAttributeWrite):

      ''' Disallow property mutation before instantiation.

          The Exception raised for invalid writes can be set
          via ``exception``.

          :param name: Name of the property we are being asked to mutate.
          :param value: Value that we are being asked to set ``name`` to.
          :param exception: Exception to be raised in the event of an error.
            Handles switchover to ``KeyError``-based exceptions if this method
            is being called from Python's item-style API.

          :raises InvalidItem: In the case that this method is used via Python's
            Item API and an invalid attempt is made to write to a property.

          :raises InvalidAttributeWrite: In the case that this method is used
            in an invalid way to attempt an attribute write.

          :returns: Generally ``None`` if a successful write is made. '''

      # cannot mutate data before instantiation
      if name in cls.__lookup__:
        raise exception('mutate', name, cls)

      # setting internal class-level properties
      if name.startswith('__'):
        return super(AbstractModel.__metaclass__, cls).__setattr__(name, value)

      # cannot create new properties before instantiation
      raise exception('create', name, cls)

    def __getitem__(cls, name, exception=exceptions.InvalidItem):

      ''' Override itemgetter syntax to return property
          objects at the class level.

          :param name: Name of the value we wish to retrieve.
          :param exception: Exception to be raised

          :raises InvalidItem: In the case of an attempt to read
            an invalid or non-existent property value.

          :returns: Value of the target property ``name``, or the
            :py:class:`model.Property` object itself if accessed
            at a class level. '''

      if name not in cls.__lookup__:
        raise exception('read', name, cls)  # cannot read non-data properties
      return cls.__dict__[name]


  class _PropertyValue(tuple):

    ''' Named-tuple class for property value bundles.
        DOCSTRING'''

    __slots__ = tuple()
    __fields__ = ('dirty', 'data')

    def __new__(_cls, data, dirty=False):

      ''' Create a new `PropertyValue` instance.

          :param data:
          :param dirty:

          :returns: '''

      return tuple.__new__(_cls, (data, dirty))  # pass up-the-chain to `tuple`

    # util: generate a string representatin of this `_PropertyValue`
    __repr__ = lambda self: "Value(%s)%s" % ((
          '"%s"' % self[0]) if isinstance(self[0], basestring)
              else self[0].__repr__(), '*' if self[1] else '')

    # util: reduce arguments for pickle
    __getnewargs__ = lambda self: tuple(self)

    # util: lock down classdict
    __dict__ = property(lambda self: dict(zip(self.__fields__, self)))

    # util: map data and dirty properties
    data = property(operator.itemgetter(0))
    dirty = property(operator.itemgetter(1))

  # = Internal Methods = #
  def __new__(cls, *args, **kwargs):

    ''' Intercepts construction requests for directly Abstract model classes.

        Args:
        Kwargs:

        :raises:

        :returns: '''

    if cls.__name__ == 'AbstractModel':  # prevent direct instantiation
      raise exceptions.AbstractConstructionFailure('AbstractModel')
    return super(AbstractModel, cls).__new__(cls, *args, **kwargs)

  # util: generate a string representation of this entity
  __repr__ = lambda self: "%s(%s, %s)" % (
      self.__kind__, self.__key__,
        ', '.join(['='.join([k, str(self.__data__.get(k, None))])
                   for k in self.__lookup__]))

  __str__ = __unicode__ = __repr__  # map repr to str and unicode

  def __setattr__(self, name, value, exception=exceptions.InvalidAttribute):

    ''' Attribute write override.

        :param name:
        :param value:
        :param exception:

        :raises:

        :returns: '''

    # internal properties, data properties and `key`
    # can be written to after construction
    if name.startswith('__') or name in self.__lookup__ or name == 'key':
      # delegate upwards for write
      return super(AbstractModel, self).__setattr__(name, value)
    raise exception('set', name, self.kind())

  def __getitem__(self, name):

    ''' Item getter support.

        :param name:

        :returns: '''

    if name not in self.__lookup__:
      # only data properties are exposed via `__getitem__`
      raise exceptions.InvalidItem('get', name, self.kind())
    return getattr(self, name)  # proxy to attribute API

  # util: support for python's item API
  __setitem__ = lambda self, item, value: (
    self.__setattr__(item, value, exceptions.InvalidItem))

  def __context__(self, _type=None, value=None, traceback=None):

    ''' Context enter/exit - apply explicit mode.

        :param _type:
        :param value:
        :param traceback:

        :returns: '''

    if traceback:  # pragma: no cover
      return False  # in the case of an exception in-context, bubble it up
    self.__explicit__ = (not self.__explicit__)  # toggle explicit status
    return self

  # util: alias context entry/exit to `__context__` toggle method
  __enter__ = __exit__ = __context__

  # util: proxy `len` to length of written data (also alias `__nonzero__`)
  __len__ = lambda self: len(self.__data__)
  __nonzero__ = __len__

  # util: `dirty` property flag, proxies to `_PropertyValue`(s) for dirtyness
  __dirty__ = property(lambda self: any(
    (dirty for value, dirty in self.__data__.itervalues())))

  # util: `persisted` property flag, indicates whether key has been persisted
  __persisted__ = property(lambda self: self.key.__persisted__)

  def __iter__(self):

    ''' Allow models to be used as dict-like generators.

        :returns: '''

    for name in self.__lookup__:
      value = self._get_value(name, default=Property._sentinel)

      # skip unset properties without a default, except in `explicit` mode
      if (value == Property._sentinel and (not self.__explicit__)):
        if self.__class__.__dict__[name]._default != Property._sentinel:
          # return a prop's default in `implicit` mode
          yield name, self.__class__.__dict__[name]._default
        continue  # pragma: no cover
      yield name, value
    raise StopIteration()

  def _set_persisted(self, flag=False):

    ''' Notify this entity that it has been persisted to storage.

        :param flag:

        :returns: '''

    self.key.__persisted__ = True
    for name in self.__data__:  # iterate over set properties
      # set value to previous, with `False` dirty flag
      self._set_value(name, self._get_value(name,
                      default=Property._sentinel), False)
    return self

  def _get_value(self, name, default=None):

    ''' Retrieve the value of a named property on this Entity.

        :param name:
        :param default:

        :raises:
        :returns: '''

    if name:  # calling with no args gives all values in (name, value) form
      if name in self.__lookup__:
        value = self.__data__.get(name, Property._sentinel)
        if not value:
          if self.__explicit__ and value is Property._sentinel:
            return Property._sentinel  # return _EMPTY sentinel in explicit mode
          return default  # return default value passed in
        return value.data  # return property value
      raise exceptions.InvalidAttribute('get', name, self.kind())
    return [(i, getattr(self, i)) for i in self.__lookup__]

  def _set_value(self, name, value=_EMPTY, _dirty=True):

    ''' Set (or reset) the value of a named property on this Entity.

        :param name:
        :param value:
        :param _dirty:

        :raises:
        :returns: '''

    if not name: return self  # empty strings or dicts or iterables return self

    if isinstance(name, (list, dict)):
      if isinstance(name, dict):
        name = name.items()  # convert dict to list of tuples
      # filter out flags from caller
      return [self._set_value(k, i, _dirty=_dirty) for k, i in name if (
                k not in ('key', '_persisted'))]

    # allow a tuple of (name, value), for use in map/filter/etc
    if isinstance(name, tuple):  # pragma: no cover
      name, value = name

    if name == 'key':  # if it's a key, set through _set_key
      return self._set_key(value).owner  # returns `self` :)

    if name in self.__lookup__:  # check property lookup
      # if it's a valid property, create a namedtuple value placeholder
      self.__data__[name] = self.__class__._PropertyValue(value, _dirty)
      return self
    raise exceptions.InvalidAttribute('set', name, self.kind())

  def _set_key(self, value=None, **kwargs):

    ''' Set this Entity's key manually.

        kwargs

        :param value:

        :raises:
        :returns: '''

    _valid_key_classes = (self.__class__.__keyclass__, tuple, basestring)

    # cannot provide both a value and formats
    if value and kwargs:
      raise exceptions.MultipleKeyValues(self.kind(), value, kwargs)

    # for a literal key value
    if value is not None:
      if not isinstance(value, _valid_key_classes):  # filter out invalid keys
        raise exceptions.InvalidKey(*(
          type(value),
          value,
          self.__class__.__keyclass__.__name__))

      # set local key from result of dict->get(<formatter>)->__call__(<value>)
      self.__key__ = {

        # return keys directly
        self.__class__.__keyclass__: lambda x: x,

        # pass tuples through `from_raw`
        tuple: self.__class__.__keyclass__.from_raw,

        # pass strings through `from_urlsafe`
        basestring: self.__class__.__keyclass__.from_urlsafe

      }.get(type(value), lambda x: x)(value)._set_internal('owner', self)

      return self.__key__  # return key

    if kwargs:  # filter out multiple formats
      formatter, value = kwargs.items()[0]
      if len(kwargs) > 1:  # disallow multiple format kwargs
        raise exceptions.MultipleKeyFormats(', '.join(kwargs.keys()))

      # resolve key converter, if any, set owner, and `__key__`, and return
      self.__key__ = {

        # for raw, pass through `from_raw`
        'raw': self.__class__.__keyclass__.from_raw,

        # for strings, pass through `from_urlsafe`
        'urlsafe': self.__class__.__keyclass__.from_urlsafe,

        # by default it's a constructed key
        'constructed': lambda x: x

      }.get(formatter, lambda x: x)(value)._set_internal('owner', self)
      return self.__key__

    # except in the case of a null value and no formatter args
    raise exceptions.UndefinedKey(value, kwargs)

  ## = Property Bindings  = ##
  key = property(lambda self: self.__key__, _set_key)  # bind model key


## == Concrete Classes == ##

## Key
class Key(AbstractKey):

  ''' Concrete Key class.
      DOCSTRING '''

  __separator__ = u':'  # separator for joined/encoded keys
  __schema__ = (_DEFAULT_KEY_SCHEMA if not (
                _MULTITENANCY) else _MULTITENANT_KEY_SCHEMA)

  ## = Internal Methods = ##
  def __new__(cls, *parts, **formats):

    ''' Constructs keys from various formats.

        args, kwargs

        :raises:
        :returns: '''

    # extract 1st-provided format
    formatter, value = (
      formats.items()[0] if formats else ('__constructed__', None))

    # disallow multiple key formats
    if len(filter(lambda x: x[0] != '_persisted', formats.iteritems())) > 1:
      raise exceptions.MultipleKeyFormats(', '.join(formats.keys()))

    return {  # delegate full-key decoding to classmethods
      'raw': cls.from_raw,
      'urlsafe': cls.from_urlsafe
    }.get(*(
      formatter,
      lambda x: super(AbstractKey, cls).__new__(cls, *parts, **formats)))(value)

  def __init__(self, *parts, **kwargs):

    ''' Initialize this Key.

        args, kwargs

        :raises:
        :returns: '''

    if len(parts) > 1:  # normal case: it's a full/partially-spec'd key

      # it's a fully- or partially-spec'ed key
      if len(parts) <= len(self.__schema__):
        _parts_diff = (len(self.__schema__) - len(parts))
        _pluck_kind = lambda x: x.kind() if hasattr(x, 'kind') else x
        mapped = zip([i for i in reversed(self.__schema__)][_parts_diff:],
                         map(_pluck_kind, parts))

      else:
        # for some reason the schema falls short of our parts
        raise exceptions.KeySchemaMismatch(*(
              self.__class__.__name__,
              len(self.__schema__),
              str(self.__schema__)))

      _pluck = lambda x: (x[0], x[1].kind()) if isinstance(x[1], Model) else x
      for name, value in map(_pluck, mapped):
        setattr(self, name, value)  # set appropriate attribute via setter

    elif len(parts) == 1:  # special case: it's a kinded, empty key
      if hasattr(parts[0], 'kind'):
        parts = (parts[0].kind(),)  # quick ducktyping: is it a model?
      self.__kind__ = parts[0]

    # if we *know* this is an existing key, `_persisted` should be `true`
    self._set_internal('parent', kwargs.get('parent'))

    # also set kwarg-passed parent.
    self._set_internal('persisted', kwargs.get('_persisted', False))

  def __setattr__(cls, name, value):

    ''' Block attribute overwrites.

        :param name:
        :param value:

        :raises:
        :returns: '''

    if not name.startswith('__'):
      if name not in cls.__schema__:
        raise exceptions.InvalidKeyAttributeWrite('create', name, cls)
      if getattr(cls, name) is not None:
        raise exceptions.InvalidKeyAttributeWrite('overwrite', name, cls)
    return super(AbstractKey, cls).__setattr__(name, value)


class VertexKey(Key):

  ''' Key class for ``Vertex`` records. '''


class EdgeKey(Key):

  ''' Key class for ``Edge`` records. '''


## Property
class Property(object):

  ''' Concrete Property class.
      DOCSTRING '''

  __metaclass__ = abc.ABCMeta  # enforce definition of `validate` for subclasses
  __slots__ = _PROPERTY_SLOTS  # setup slots for property options
  _sentinel = _EMPTY  # default sentinel for basetypes/values

  ## = Internal Methods = ##
  def __init__(self, name, basetype,
                           default=_sentinel,
                           required=False,
                           repeated=False,
                           indexed=True,
                           **options):

    ''' Initialize this Property.

        kwargs

        :param name:
        :param basetype:
        :param default:
        :param required:
        :param repeated:
        :param indexed:

        :raises:
        :returns: '''

    # copy locals specified above onto object properties of the same name,
    # specified in `self.__slots__`
    map(lambda args: setattr(self, *args), (
          zip(self.__slots__, (
            name, options, indexed, required, repeated, basetype, default))))

  ## = Descriptor Methods = ##
  def __get__(self, instance, owner):

    ''' Descriptor attribute access.

        :param instance:
        :param owner:

        :raises:
        :returns: '''

    if instance:  # proxy to internal entity method.

      # grab value, returning special
      # a) property default or
      # b) sentinel if we're in explicit mode and it is unset
      if self._default != Property._sentinel:  # we have a set default
        value = instance._get_value(self.name, default=self._default)
      else:
        value = instance._get_value(self.name, default=Property._sentinel)

      return None if (not value and (value == Property._sentinel) and
                      instance.__explicit__ is False) else value

    # otherwise, class-level access is always the property in question
    return self

  def __set__(self, instance, value):

    ''' Descriptor attribute write.

        :param instance:
        :param value:

        :raises:
        :returns: '''

    if instance is not None:  # only allow data writes after instantiation
      # delegate to `AbstractModel._set_value`
      return instance._set_value(self.name, value)
    raise exceptions.InvalidAttributeWrite('set', self.name, self.kind)

  # delegate to `__set__` to clear the property
  __delete__ = lambda self, instance: instance.__set__(instance, None)

  def valid(self, instance):

    ''' Validate the value of this property, if any.

        :param instance:

        :raises:
        :returns: '''

    if self.__class__ != Property and hasattr(self, 'validate'):
      # check for subclass-defined validator to delegate validation to
      return self.validate(instance)

    value = instance._get_value(self.name)  # retrieve value

    # check required-ness
    if (value in (None, self._sentinel)):
      if self._required:
        raise exceptions.PropertyRequired(self.name, instance.kind())
      # empty value, non-required, all good :)
      if value is self._sentinel: return True

    if isinstance(value, (list, tuple, set, frozenset)):  # check multi-ness
      if not self._repeated:
        raise exceptions.PropertyNotRepeated(self.name, instance.kind())
    else:
      if self._repeated:
        raise exceptions.PropertyRepeated(self.name, instance.kind())
      value = (value,)  # make value iterable

    for v in value:  # check basetype

      # it validates if:
      # 1) the field is typeless, or
      # 2) the value is `None` or an instance of it's basetype
      if self._basetype is None or (
        (v is not self._sentinel) and isinstance(v, (
                                      self._basetype, type(None)))):
        continue
      raise exceptions.InvalidPropertyValue(*(
        self.name, instance.kind(), type(v).__name__, self._basetype.__name__))
    return True  # validation passed! :)

  def __repr__(self):

    ''' Generate a string representation
      of this :py:class:`Property`.

      :returns: Stringified, human-readable
      value describing this :py:class:`Property`. '''

    return "%s(%s, type=%s)" % (
      self.__class__.__name__, self.name, self._basetype.__name__)

  __unicode__ = __str__ = __repr__

  # util method to clone `Property` objects
  clone = lambda self: self.__class__(self.name, self._basetype, self._default,
                                      self._required, self._repeated,
                                      self._indexed, **self._options)

  ## == Query Overrides (Operators) == ##
  __sort__ = lambda self, direction: (  # internal sort spawn
    query.Sort(self, operator=(direction or query.Sort.ASCENDING)))
  __filter__ = lambda self, other, operator: (  # internal filter spawn
    query.Filter(self, other, operator=(operator or query.Filter.EQUALS)))

  ## == Sort Spawn == ##
  __pos__ = lambda self: (
    self.__sort__(query.Sort.ASCENDING))  # `+` operator
  __neg__ = lambda self: (
    self.__sort__(query.Sort.DESCENDING))  # `-` operator

  ## == Filter Spawn == ##
  __eq__ = lambda self, other: (
    self.__filter__(other, query.Filter.EQUALS))  # `==` operator
  __ne__ = lambda self, other: (
    self.__filter__(other, query.Filter.NOT_EQUALS))  # `!=` operator
  __gt__ = lambda self, other: (
    self.__filter__(other, query.Filter.GREATER_THAN))  # `>` operator
  __ge__ = lambda self, other: (
    self.__filter__(other, query.Filter.GREATER_THAN_EQUAL_TO))  # `>=` operator
  __lt__ = lambda self, other: (
    self.__filter__(other, query.Filter.LESS_THAN))  # `<` operator
  __le__ = lambda self, other: (
    self.__filter__(other, query.Filter.LESS_THAN_EQUAL_TO))  # `<=` operator


class Model(AbstractModel):

  ''' Concrete Model class. '''

  __keyclass__ = Key

  ## = Internal Methods = ##
  def __init__(self, **properties):

    ''' Initialize this Model.

        args

        :raises:
        :returns: '''

    # grab key / persisted flag, if any, and set explicit flag to `False`
    self.__explicit__, self.__initialized__ = False, True

    # initialize key, internals, and map any kwargs into data
    self.key, self.__data__ = (
      properties.get('key') or self.__keyclass__(self.kind(), _persisted=False),
      {})

    self._set_value(properties, _dirty=(not properties.get('_persisted')))

  ## = Class Methods = ##
  kind = classmethod(lambda cls: cls.__name__)


class Vertex(Model):

  ''' Concrete Vertex class.
      DOCSTRING '''

  __owner__, __keyclass__ = 'Vertex', VertexKey

  class __metaclass__(AbstractModel.__metaclass__):

    ''' DOCSTRING '''

    def __gt__(cls, target):

      ''' Syntactic sugar for creating an on-the-fly
          :py:class:`Edge` subclass.

          Overrides the syntax:
            ``class Friends(Person > Person): [...]```

          :param other: Target :py:class:`Vertex` subclass
            to factory an :py:class:`Edge` to.

          :returns: Factoried :py:class:`Edge` subclass that
            represents a type connecting ``self`` to ``other``. '''

      return cls.to(target, directed=False)

    def __lt__(cls, origin):

      ''' Syntactic sugar for creating an on-the-fly
          :py:class:`Edge` subclass.

          Overrides the syntax:
            ``class Supporting(Organization < Person): [...]```

          :param other: Target :py:class:`Vertex` subclass
            to factory an :py:class:`Edge` to.

          :returns: Factoried :py:class:`Edge` subclass that
            represents a type connecting ``self`` to ``other``. '''

      return origin.to(cls, directed=False)

    def __rshift__(cls, target):

      ''' Syntactic sugar for creating an on-the-fly
          :py:class:`Edge` subclass. This syntactic
          extension spawns a **directed** ``Edge``.

          Overrides the syntax:
            ``class Comment(Person >> Post): [...]```

          :param other: Target :py:class:`Vertex` subclass
            to factory an :py:class:`Edge` to.

          :returns: Factoried :py:class:`Edge` subclass that
            represents a type connecting ``self`` to ``other``. '''

      return cls.to(target, directed=True)

    def __lshift__(cls, origin):

      ''' Syntactic sugar for creating an on-the-fly
          :py:class:`Edge` subclass. This syntactic
          extension spawns a **directed** ``Edge``.

          Overrides the syntax:
            ``class Contribution(Legislator << Contributor): [...]```

          :param other: Target :py:class:`Vertex` subclass
            to factory an :py:class:`Edge` to.

          :returns: Factoried :py:class:`Edge` subclass that
            represents a type connecting ``self`` to ``other``. '''

      return origin.to(cls, directed=True)

  @classmethod
  def to(cls, *targets, **options):

    ''' Syntactic sugar for creating an on-the-fly
        :py:class:`Edge` subclass.

        :param target: Target :py:class:`Vertex` subclass
          to factory an :py:class:`Edge` to.

        :param directed: Whether the target :py:class:`Edge`
          subclass should be considered directional in nature.

        :raises TypeError: In the case that a non-``Vertex``
          is passed for ``target``.

        :returns: Factoried :py:class:`Edge` subclass that
          represents a type connecting ``self`` to ``other``. '''

    # classes only plz
    for target in targets:
      if not issubclass(target, Vertex):
        raise TypeError("Vertices can only point to other Vertices."
                        " An Edge from `%s` to `%s` was requested, but `%s` is"
                        " not a Vertex." % (cls, target, target))

    return Edge.__spec_class__(cls, targets, options.get('directed', False))


class EdgeSpec(object):

  ''' Specifies the peering and directed-ness
      of an :py:class:`Edge`. '''

  __slots__ = ('origin', 'peering', 'directed')

  def __new__(cls, name=None, bases=None, pmap=None):

    '''  '''

    # subtype construction generates ``Edge`` subclasses
    if name and bases and isinstance(pmap, dict):
      return type(name, (Edge,), dict(pmap or {}, __spec__=bases[0]))

    # different signature if we're not constructing (for clarity)
    origin, peering, directed = name, bases, pmap

    # allow construction as well (for use as a config symbol, essentially)
    return object.__new__(cls, origin, peering, directed)

  def __init__(self, origin, peering, directed):

    ''' Initialize an ``EdgeSpec`` class, according
        to the specified ``peering`` configuration.

        :param origin:

        :param peering: An ordered iterable of ``Vertex``
          subclasses to connect via an ``Edge``, where
          index ``0`` is always considered the **origin**
          and the remaining items are targets that can
          be validly connected to **origin**.

        :param directed: Flag (``bool``) indicating that
          this ``Edge`` represents a directional
          relationship between each ``origin -> target``
          pair. '''

    if not len(peering) > 0:
      raise TypeError('Cannot specify an `Edge` without at'
                      ' least one target.')

    self.origin, self.peering, self.directed = (
      origin, peering[0] if len(peering) == 1 else peering, directed)

  def __repr__(self):

    ''' Generate a string representation for the
        relationship specified by this ``EdgeSpec``
        class.

        :returns: String, like ``(origin <-> target, ...)``
          (if undirected), otherwise ``(origin -> target, ...)``
          (if directed). '''

    return "(%s %s %s)" % (
      self.origin.kind(), '<->' if not self.directed else '->', (
        self.peering.kind() if issubclass(self.peering, Model) else ', '.join((
          k.kind() for k in self.peering))))


class Edge(Model):

  ''' Concrete Edge class.
      DOCSTRING '''

  __owner__, __keyclass__ = 'Edge', EdgeKey


  class __metaclass__(Model.__metaclass__):

    ''' DOCSTRING '''

    @classmethod
    def initialize(cls, name, bases, pmap):

      ''' DOCSTRING '''

      if '__spec__' in pmap and pmap['__spec__'].directed:
        pmap['source'] = Vertex, {'indexed': True}
        pmap['target'] = Vertex, {'indexed': True, 'repeated': True}
      elif '__spec__' not in pmap or (
           '__spec__' in pmap and not pmap['__spec__'].directed):
        pmap['peers'] = Vertex, {'indexed': True, 'repeated': True}

      return super(cls, cls).initialize(name, bases, pmap)

  __spec_class__ = EdgeSpec

  ## = Internal Methods = ##
  def __init__(self, source=None, *targets, **properties):

    ''' Initialize this ``Edge`` with a ``Vertex``
        ``source`` and ``target`` pair.

        :param pair_or_source:
        :param maybe_target:
        :param **properties:

        :raises:
        :returns: '''

    if (source is None or not targets) and not properties.get('_persisted'):
      raise TypeError('Constructing an `Edge` requires at least'
                      ' one `source` and `target`, or one pair'
                      ' (`source`, `target`).')

    if hasattr(self, '__spec__') and self.__spec__.directed:
      properties['source'], properties['target'] = (
        source, targets)
    else:
      properties['peers'] = tuple([source] + list(targets))

    super(Edge, self).__init__(**properties)


# Module Globals
__abstract__ = (
  abstract,
  MetaFactory,
  AbstractKey,
  AbstractModel
)

__concrete__ = (
  concrete,
  Property,
  KeyMixin,
  ModelMixin,
  Key,
  Model,
  Vertex,
  Edge
)

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
  'Vertex',
  'Edge',
  'adapter',
  'exceptions'
)
