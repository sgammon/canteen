# -*- coding: utf-8 -*-

'''

  canteen: abstract model adapters
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''


# stdlib
import abc
import zlib
import time
import json
import base64
import logging
import datetime

# canteen utils
from canteen.util import config
from canteen.util import decorators


## Globals
_adapters = {}
_adapters_by_model = {}
_encoder = base64.b64encode  # encoder for key names and special strings, if enabled
_compressor = zlib  # compressor for data values, if enabled
_core_mixin_classes = ('Mixin', 'KeyMixin', 'ModelMixin', 'CompoundKey', 'CompoundModel')

## Computed Classes
CompoundKey = None
CompoundModel = None


class ModelAdapter(object):

  ''' Abstract base class for classes that adapt apptools models to a particular storage backend. '''

  registry = {}
  __metaclass__ = abc.ABCMeta

  @property
  def config(self):  # pragma: no cover

    ''' Cached config shortcut.
      :returns: Configuration ``dict``, if any. Defaults to ``{'debug': True}``. '''

    return config.Config().get(self.__class__.__name__, {'debug': True})

  @decorators.classproperty
  def logging(cls):

    ''' Named logging pipe.
      :returns: Customized :py:mod:`apptools.util.debug.AppToolsLogger` instance,
            with a proper ``name``/``path``/``condition``. '''

    #return debug.AppToolsLogger(**{
    #  'path': '.'.join(psplit[0:-1]),
    #  'name': psplit[-1]})._setcondition(cls.config.get('debug', True))
    return logging

  @decorators.classproperty
  def serializer(cls):

    ''' Load and return the appropriate serialization codec. This
      property is mainly meant to be overridden by child classes.

      :returns: Current serializer, defaults to :py:mod:`json`. '''

    # default to JSON
    return json

  @decorators.classproperty
  def encoder(cls):  # pragma: no cover

    ''' Encode a stringified blob for storage. This property
      is mainly meant to be overridden by child classes.

      :returns: Current :py:data:`_encoder`, defaults to :py:mod:`base64`. '''

    # use local encoder
    return _encoder

  @decorators.classproperty
  def compressor(cls):  # pragma: no cover

    ''' Load and return the appropriate compression codec. This
      property is mainly meant to be overridden by child classes.

      :returns: Current :py:mod:`_compressor`, defaults to :py:mod:`zlib`. '''

    return _compressor

  ## == Internal Methods == ##
  def _get(self, key, **kwargs):

    ''' Low-level method for retrieving an entity by Key. Fetches and deserializes
      the given entity, if it exists, or returns ``None``.

      :param key: Instance of :py:class:`model.Key` to retrieve from storage.
      :raises RuntimeError: If the target :py:class:`model.adapter.ModelAdapter`
                  does not implement ``get()``, which is an ABC-enforced
                  child class method. :py:exc:`RuntimeError` and descendents
                  are also re-raised from the concrete adapter.
      :returns: Inflated :py:class:`model.Model` instance, corresponding to ``key``,
            or ``None`` if no such entity could be found. '''

    if self.config.get('debug', False):  # pragma: no cover
      self.logging.info("Retrieving entity with Key: \"%s\"." % key)

    # immediately fail with no overriden `get`
    if not hasattr(self.__class__, 'get') and self.__class__ != ModelAdapter:  # pragma: no cover
      raise RuntimeError("ModelAdapter `%s` does not implement `get`,"
                 "and thus cannot be used for reads." % self.__class__.__name__)
    else:
      # grab getter method
      getter = getattr(self.__class__, 'get')

    # flatten key into stringified repr
    joined, flattened = key.flatten(True)
    parent, kind, id = flattened

    # optionally allow adapter to encode key
    encoded = self.encode_key(joined, flattened)

    if not encoded:
      # otherwise, use regular base64 via `AbstractKey`
      encoded = key.urlsafe(joined)

    # pass off to delegated `get`
    try:
      entity = getter((encoded, flattened), **kwargs)
    except RuntimeError:  # pragma: no cover
      raise
    else:
      if entity is None:
        return  # not found

      # inflate key + model and return
      key.__persisted__ = True
      entity['key'] = key
      return self.registry[kind](_persisted=True, **entity)

  def _put(self, entity, **kwargs):

    ''' Low-level method for persisting an Entity. Collapses and serializes
      the target ``entity`` into native types and delegates to the active
      :py:class:`model.adapter.ModelAdapter` for storage.

      :param entity: Object descendent of :py:class:`model.Model`, suitable for
               storage via the currently-active adapter.
      :raises ValueError: In the case of an unknown or unregistered *kind*.
      :returns: New (or updated) key value for the target ``entity``. '''

    # resolve model class
    _model = self.registry.get(entity.kind())
    if not _model: raise ValueError('Could not resolve model class "%s".' % entity.kind())

    with entity:  # enter explicit mode

      # validate entity, will raise validation exceptions
      for name, value in entity.to_dict(_all=True).items():
        _model.__dict__[name].valid(entity)

      # resolve key if we have a zero-y key or key class
      if not entity.key or entity.key is None:
        # build an ID-based key
        ids = self.allocate_ids(_model.__keyclass__, entity.kind())
        entity._set_key(_model.__keyclass__(entity.kind(), ids))

      # flatten key/entity
      joined, flattened = entity.key.flatten(True)

    # delegate
    return self.put((self.encode_key(joined, flattened) or entity.key.urlsafe(joined), flattened),
            entity._set_persisted(True), _model, **kwargs)

  def _delete(self, key, **kwargs):

    ''' Low-level method for deleting an entity by Key.

      :param key: Target :py:class:`model.Key` to delete.
      :returns: Result of the delete operation. '''

    if self.config.get('debug', False):  # pragma: no cover
      self.logging.info("Deleting Key: \"%s\"." % key)

    joined, flattened = key.flatten(True)
    return self.delete((self.encode_key(joined, flattened) or key.urlsafe(joined), flattened), **kwargs)

  @classmethod
  def _register(cls, model):

    ''' Low-level method for registering a Model class with
      this adapter's registry.

      :param model: :py:class:`model.Model` class to register.
      :returns: The ``model`` it was handed (for chainability). '''

    cls.registry[model.kind()] = model
    return model

  ## == Class Methods == ##
  @classmethod
  def acquire(cls, name, bases, properties):

    ''' Acquire a new/existing copy of this adapter. Available
      for override by child classes to customize the driver
      acquisition process. Passed an identical signature to
      ``type``, *before* the :py:class:`model.Model` class
      has been fully-built.

      :param name: String name of the new :py:class:`model.Model` class-to-be.
      :param bases: Tuple of base classes for the target :py:class:`model.Model`.
      :param properties: Property ``dict`` from class definition.
      :returns: The "acquired" adapter object. '''

    global _adapters
    global _adapters_by_model

    # if we don't have one yet, spawn a singleton
    if cls.__name__ not in _adapters:
      _adapters[cls.__name__] = cls()
    _adapters_by_model[name] = _adapters[cls.__name__]
    return _adapters[cls.__name__]

  ## == Abstract Methods == ##
  @abc.abstractmethod
  def get(cls, key, **kwargs):  # pragma: no cover

    ''' Retrieve an entity by :py:class:`model.Key`. Must accept a
      tuple in the formatv``(<joined Key repr>, <flattened key>)``.
      Abstract method that **must** be overridden by concrete
      implementors of :py:class:`ModelAdapter`.

      :param key: Target :py:class:`model.Key` to retrieve.
      :raises: :py:exc:`NotImplementedError`, as this method is abstract. '''

    raise NotImplementedError()

  @abc.abstractmethod
  def put(cls, key, entity, model, **kwargs):  # pragma: no cover

    ''' Persist an entity in storage. Must accept a :py:class:`model.Key`,
      which may not have an ID, in which case one is allocated. The entity
      and :py:class:`model.Model` class are also passed in.

      This method is abstract and **must** be overridden by concrete
      implementors of :py:class:`ModelAdapter`.

      :param key: Potentially-empty :py:class:`model.Key` for the new entity.
      :param entity: Object :py:class:`model.Model` to persist in storage.
      :param model: :py:class:`model.Model` class for target ``entity``.
      :raises: :py:exc:`NotImplementedError`, as this method is abstract. '''

    raise NotImplementedError()

  @abc.abstractmethod
  def delete(cls, key, **kwargs):  # pragma: no cover

    ''' Delete an entity by :py:class:`model.Key`. Must accept a target
      ``key``, whose associated entity will be deleted.

      This method is abstract and **must** be overridden by concrete
      implementors of :py:class:`ModelAdapter`.

      :param key: Target :py:class:`model.Key` to delete.
      :raises: :py:exc:`NotImplementedError`, as this method is abstract. '''

    raise NotImplementedError()

  @abc.abstractmethod
  def allocate_ids(cls, key_class, kind, count=1, **kwargs):  # pragma: no cover

    ''' Allocate new :py:class:`model.Key` IDs for ``kind`` up to
      ``count``. This method is abstract and **must** be overridden
      by concrete implementors of :py:class:`ModelAdapter`.

      :param key_class: :py:class:`model.Key` class for provisioned IDs.
      :param kind: String ``kind`` name from :py:class:`model.Model` class.
      :param count: Count of IDs to provision, defaults to ``1``.
      :raises: :py:exc:`NotImplementedError`, as this method is abstract. '''

    raise NotImplementedError()

  @classmethod
  def encode_key(cls, key, joined=None, flattened=None):  # pragma: no cover

    ''' Encode a :py:class:`model.Key` for storage. This method is
      abstract and *should* be overridden by concrete implementors
      of :py:class:`ModelAdapter`.

      In the case that a :py:class:`ModelAdapter` wishes to defer
      to the default encoder (:py:mod:`base64`), it can return ``False``.

      :param key: Target :py:class:`model.Key` to encode.
      :param joined: Joined/stringified key.
      :param flattened: Flattened ``tuple`` (raw) key.
      :returns: The encoded :py:class:`model.Key`, or ``False`` to
            yield to the default encoder. '''

    return False  # by default, yield to key b64 builtin encoding


## IndexedModelAdapter
# Adapt apptools models to a storage backend that supports indexing.
class IndexedModelAdapter(ModelAdapter):

  ''' Abstract base class for model adapters that support additional indexing APIs. '''

  # magic prefixes
  _key_prefix = '__key__'
  _kind_prefix = '__kind__'
  _group_prefix = '__group__'
  _index_prefix = '__index__'
  _reverse_prefix = '__reverse__'

  ## Indexer
  # Holds routines and data type tools for indexing apptools models in Redis.
  class Indexer(object):

    ''' Holds methods for indexing and handling index data types. '''

    _magic = {
      'key': 0x1,  # magic ID for `model.Key` references
      'date': 0x2,  # magic ID for `datetime.date` instances
      'time': 0x3,  # magic ID for `datetime.time` instances
      'datetime': 0x4  # magic ID for `datetime.datetime` instances
    }

    @classmethod
    def convert_key(cls, key):

      ''' Convert a :py:class:`model.Key` to an indexable value.

        :param key: Target :py:class:`model.Key` to conver.
        :returns: Tupled ``(<magic key code>, <flattened key>)``,
              suitable for adding to the index. '''

      # flatten and return key structure with magic
      joined, flattened = key.flatten(True)
      return (cls._magic['key'], map(lambda x: x is not None, flattened))

    @classmethod
    def convert_date(cls, _date):

      ''' Convert a Python ``date`` to an indexable value.

        :param date: Python ``date`` to convert.
        :returns: Tupled ``(<magic date code>, <flattened date>)`` to add to the index. '''

      # convert to ISO format, return date with magic
      return (cls._magic['date'], _date.isoformat())

    @classmethod
    def convert_time(cls, _time):

      ''' Convert a Python ``time`` to an indexable value.

        :param _time: Python ``time`` to convert.
        :returns: Tupled ``(<magic time code>, <flattened time>)``, suitable
              for addition to the index. '''

      # convert to ISO format, return time with magic
      return (cls._magic['time'], _time.isoformat())

    @classmethod
    def convert_datetime(cls, _datetime):

      ''' Convert a Python ``datetime`` to an indexable value.

        :param _datetime: Python ``datetime`` to convert.
        :returns: Tupled ``(<magic time code>, <flattened datetime>)``,
              suitable for addition to the index. '''

      # convert to integer, return datetime with magic
      return (cls._magic['datetime'], int(time.mktime(_datetime.timetuple())))

  @decorators.classproperty
  def _index_basetypes(self):

    ''' Map basetypes to indexer routines.
      :returns: Default basetype ``dict``. '''

    from canteen import model

    return {

      # -- basetypes -- #
      int: self.serializer.dumps,
      bool: self.serializer.dumps,
      long: self.serializer.dumps,
      float: self.serializer.dumps,
      basestring: self.serializer.dumps,

      # -- model/key types -- #
      model.Key: self.Indexer.convert_key,

      # -- date/time types -- #
      datetime.date: self.Indexer.convert_date,
      datetime.time: self.Indexer.convert_time,
      datetime.datetime: self.Indexer.convert_datetime

    }

  def _put(self, entity, **kwargs):

    ''' Hook to trigger index writes for a given entity. Defers
      up the chain to :py:class:`ModelAdapter` after generating
      (and potentially writing) a set of indexes from the target
      ``entity``.

      :param entity: Entity :py:class:`model.Model` to persist.
      :returns: Resulting :py:class:`model.Key` from write operation. '''

    # small optimization - with a deterministic key, we can parrellelize
    # index writes (assuming async is supported in the underlying driver)

    _indexed_properties = self._pluck_indexed(entity)

    # delegate write up the chain
    written_key = super(IndexedModelAdapter, self)._put(entity, **kwargs)

    # proxy to `generate_indexes` and write indexes
    if not _indexed_properties:
      origin, meta = self.generate_indexes(entity.key)
      property_map = {}
    else:
      origin, meta, property_map = self.generate_indexes(entity.key, _indexed_properties)

    self.write_indexes((origin, meta, property_map), **kwargs)

    # delegate up the chain for entity write
    return written_key

  def _delete(self, key, **kwargs):

    ''' Hook to trigger index cleanup for a given key. Defers
      up the chain to :py:class:`ModelAdapter` after generating
      a set of indexes to clean for the target ``key``.

      :param key: Target :py:class:`model.Key` to delete.
      :returns: Result of delete operation. '''

    # generate meta indexes only, then clean
    self.clean_indexes(self.generate_indexes(key))

    # delegate delete up the chain
    return super(IndexedModelAdapter, self)._delete(key)

  def _pluck_indexed(self, entity):

    ''' Zip and pluck only properties that should be indexed.
      Simply returns a set of property descriptors, mapped to
      ehtir names in a ``dict``, if they are marked as
      needing to be indexed.

      :param entity: Target entity to produce indexes for.
      :returns: Map ``dict`` of properties to index. '''

    _map = {}

    # grab only properties enabled for indexing
    for k, v in filter(lambda x: entity.__class__.__dict__[x[0]]._indexed, entity.to_dict().items()):
      _map[k] = (entity.__class__.__dict__[k], v)  # attach property name, property class, value

    return _map

  @classmethod
  def generate_indexes(cls, key, properties=None):

    ''' Generate a set of indexes that should be written to
      with associated values.

      :param key: Target :py:class:`model.Key` to index.
      :param properties: Entity :py:class:`model.Model` property
      values to index.
      :returns: Tupled set of ``(encoded_key, meta_indexes, property_indexes)``. '''

    _property_indexes, _meta_indexes = [], []

    if key is not None:

      # provision vars, generate meta indexes
      encoded_key = cls.encode_key(*key.flatten(True)) or key.urlsafe()
      _meta_indexes.append((cls._key_prefix,))
      _meta_indexes.append((cls._kind_prefix, key.kind))  # map kind to encoded key

      # consider ancestry
      if not key.parent:

        # generate group indexes in the case of a nonvoid parent
        _meta_indexes.append((cls._group_prefix,))

      else:

        # append keyparent-based group prefix
        root_key = [i for i in key.ancestry][0]

        # encode root key
        encoded_root_key = cls.encode_key(root_key) or root_key.urlsafe()

        _meta_indexes.append((cls._group_prefix, encoded_root_key))

    # add property index entries
    if properties:

      # we're applying writes
      for k, v in properties.items():

        # extract property class and value
        prop, value = v

        # consider repeated properties
        if not prop._repeated or not isinstance(value, (tuple, list, set, frozenset)):
          value = [value]

        # iterate through property values
        for v in value:
          context = (cls._index_prefix, key.kind, k, v)
          _property_indexes.append((cls._index_basetypes.get(prop._basetype, basestring), context))

        continue

    else:
      # we're cleaning indexes
      return encoded_key, _meta_indexes

    if key is not None:
      # we're writing indexes
      return encoded_key, _meta_indexes, _property_indexes
    return _property_indexes  # we're generating properties only

  @abc.abstractmethod
  def write_indexes(cls, writes, **kwargs):  # pragma: no cover

    ''' Write a batch of index updates generated earlier
      via :py:meth:`generate_indexes`. This method is
      abstract and **must** be overridden by concrete
      implementors of :py:class:`IndexedModelAdapter`.

      :param writes: Batch of index writes to commit,
               generated via :py:meth:`generate_indexes`.
      :raises: :py:exc:`NotImplementedError`, as this method is abstract. '''

    raise NotImplementedError()

  @abc.abstractmethod
  def clean_indexes(cls, key, **kwargs):  # pragma: no cover

    ''' Clean indexes and index entries matching a
      particular :py:class:`model.Key`. This method is
      abstract and **must** be overridden by concrete
      implementors of :py:class:`IndexedModelAdapter`.

      :param key: Target :py:class:`model.Key` to clean
            indexes for.
      :raises: :py:exc:`NotImplementedError`, as this method is abstract. '''

    raise NotImplementedError()

  @abc.abstractmethod
  def execute_query(cls, kind, spec, options, **kwargs):  # pragma: no cover

    ''' Execute a query, specified by ``spec``, across
      one (or multiple) indexed properties.

      :param spec: Object specification (:py:class:`model.Query`)
             specifying the query to satisfy..
      :raises: :py:exc:`NotImplementedError`, as this method is abstract. '''

    raise NotImplementedError()


## Mixin
# Metaclass for registering mixins and applying them later.
class Mixin(object):

  ''' Abstract parent for detecting and registering `Mixin` classes. '''

  __slots__ = tuple()

  class __metaclass__(type):

    ''' Local `Mixin` metaclass for registering encountered `Mixin`(s). '''

    ## == Mixin Registry == ##
    _compound = {}
    _mixin_lookup = set()
    _key_mixin_registry = {}
    _model_mixin_registry = {}

    def __new__(cls, name, bases, properties):

      ''' Factory a new registered :py:class:`Mixin`. Registers the target
        ``Mixin`` in :py:attr:`Mixin.__metaclass__._mixin_lookup`, and
        extends compound class at :py:attr:`Mixin.__metaclass__._compound`.

        :param name: Name of ``Mixin`` class to construct.
        :param bases: Class bases of ``Mixin`` class to construct.
        :param properties: Mapping ``dict`` of class properties.
        :raises RuntimeError: For invalid inheritance between mixin bases.
        :returns: Constructed ``Mixin`` class. '''

      # apply local metaclass to factoried concrete children
      klass = super(cls, cls).__new__(cls, name, bases, properties)

      # register mixin if it's not a concrete parent and is unregistered
      if name not in frozenset(_core_mixin_classes) and name not in cls._mixin_lookup:
        if KeyMixin not in bases and ModelMixin not in bases:
          ## we can only directly extend `Mixin` from `KeyMixin` and `ModelMixin`
          raise RuntimeError("Cannot directly extend `Mixin` - you must extend `KeyMixin` or `ModelMixin`.")
        elif len(bases) > 1:
          for base in bases:
            if base not in frozenset((KeyMixin, ModelMixin)):
              ## mixins are only allowed to _directly_ extend `KeyMixin` or `ModelMixin`
              raise RuntimeError("Cannot inject classes for inheritance in between"
                         " `KeyMixin` or `ModelMixin` and a concrete mixin class,"
                         " or after a concrete mixin class.")

        # add to each registry that the mixin supports
        for base in bases:

          ## add mixin to parent registry
          base.__registry__[name] = klass

        # add to global mixin lookup to prevent double loading
        cls._mixin_lookup.add(name)

        # see if we already have a compound class (mixins loaded after models)
        if Mixin._compound.get(cls):

          ## extend class dict if we already have one
          Mixin._compound.__dict__.update(dict(cls.__dict__.items()))

      return klass

    def __repr__(cls):

      ''' Generate a string representation of a `Mixin` subclass.
        :returns: String *repr* for ``Mixin`` class. '''

      return "Mixin(%s.%s)" % (cls.__module__, cls.__name__)

  internals = __metaclass__

  @decorators.classproperty
  def methods(cls):

    ''' Recursively return all available ``Mixin`` methods.
      :yields: Each method in each ``Mixin``. '''

    for component in cls.components:
      for method, func in component.__dict__.items():
        yield method, func

  @decorators.classproperty
  def compound(cls):

    ''' Generate a compound ``Mixin`` class. Builds a new class,
      composed of all available methods on attached mixins.

      :returns: Factoried compound ``Mixin`` class. '''

    if isinstance(cls.__compound__, basestring):

      # if we've never generated a `CompoundModel` or if it's been changed, regenerate...
      cls.__compound__ = globals()[cls.__compound__.__name__] = cls.internals._compound[cls] = type(*(
        cls.__compound__,
        (cls, object),
        dict([
          ('__origin__', cls),
          ('__slots__', tuple()),
        ] + [(k, v) for k, v in cls.methods])
      ))

    return cls.__compound__

  @decorators.classproperty
  def components(cls):

    ''' Return registered ``Mixin`` classes for the current ``cls``.
      :yields: Each mixin in the registry. '''

    for mixin in cls.__registry__.itervalues(): yield mixin


## KeyMixin
# Extendable, registered class that mixes in attributes to `Key`.
class KeyMixin(Mixin):

  ''' Allows injection of attributes into `Key`. '''

  __slots__ = tuple()
  __compound__ = 'CompoundKey'
  __registry__ = Mixin._key_mixin_registry


## ModelMixin
# Extendable, registered class that mixes in attributes to `Model`.
class ModelMixin(Mixin):

  ''' Allows injection of attributes into `Model`. '''

  __slots__ = tuple()
  __compound__ = 'CompoundModel'
  __registry__ = Mixin._model_mixin_registry


__all__ = (
  'CompoundKey',
  'CompoundModel',
  'ModelAdapter',
  'IndexedModelAdapter',
  'Mixin',
  'KeyMixin',
  'ModelMixin'
)
