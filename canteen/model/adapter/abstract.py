# -*- coding: utf-8 -*-

"""

  abstract model adapters
  ~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""


# stdlib
import abc
import time
import json
import base64
import logging
import datetime

# canteen utils
from canteen.util import config
from canteen.util import decorators


try:
  import zlib; _compressor = zlib
except ImportError:  # pragma: no cover
  pass  # pragma: no cover

try:
  import lz4; _compressor = lz4
except ImportError:  # pragma: no cover
  pass  # pragma: no cover

try:
  import snappy; _compressor = snappy
except ImportError:  # pragma: no cover
  pass  # pragma: no cover


## Globals
_adapters = {}
_adapters_by_model = {}
_compressor = None  # compressor for data marked for compression
_encoder = base64.b64encode  # encoder for key names and special strings
_core_mixin_classes = (
    'Mixin',
    'KeyMixin', 'ModelMixin',
    'CompoundKey', 'CompoundModel',
    'VertexMixin', 'EdgeMixin',
    'CompoundVertex', 'CompoundEdge')

## Computed Classes
CompoundKey = CompoundModel = CompoundVertex = CompoundEdge = None


class ModelAdapter(object):

  """ Abstract base class for classes that adapt canteen models to a particular
      storage backend. """

  registry = {}
  __metaclass__ = abc.ABCMeta

  @decorators.classproperty
  def config(cls):  # pragma: no cover

    """ Cached config shortcut.

        :returns: Configuration ``dict``, if any. Defaults
          to ``{'debug': True}``. """

    return config.Config().get(cls.__name__, {'debug': True})

  # noinspection PyMethodParameters
  @decorators.classproperty
  def logging(cls):

    """ Named logging pipe.

        :returns: Customized :py:mod:`canteen.util.debug.Logger`
          instance, with a ``name``/``path``/``condition``. """

    return logging  # @TODO(sgammon): proper logging

  @decorators.classproperty
  def serializer(cls):

    """ Load and return the appropriate serialization codec. This property is
        mainly meant to be overridden by child classes.

        :returns: Current serializer, defaults to :py:mod:`json`. """

    return json  # default to JSON

  @decorators.classproperty
  def encoder(cls):  # pragma: no cover

    """ Encode a stringified blob for storage. This property is mainly meant to
        be overridden by child classes.

        :returns: Current :py:data:`_encoder`, defaults to :py:mod:`base64`. """

    return _encoder  # use local encoder

  @decorators.classproperty
  def compressor(cls):  # pragma: no cover

    """ Load and return the appropriate compression codec. This property is
        mainly meant to be overridden by child classes.

        :returns: Current :py:mod:`_compressor`, defaults to :py:mod:`zlib`. """

    return _compressor

  ## == Internal Methods == ##
  def _get(self, key, **kwargs):

    """ Low-level method for retrieving an entity by Key. Fetches and
        deserializes the given entity, if it exists, or returns ``None``.

        :param key: Instance of :py:class:`model.Key` to retrieve from storage.

        :raises RuntimeError: If the target :py:class:`adapter.ModelAdapter`
          does not implement ``get()``, which is an ABC-enforced child class
          method. :py:exc:`RuntimeError` and descendents are also re-raised from
          the concrete adapter.

        :returns: Inflated :py:class:`model.Model` instance, corresponding to
            ``key``, or ``None`` if no such entity could be found. """

    if self.config.get('debug', False):  # pragma: no cover
      self.logging.info("Retrieving entity with Key: \"%s\"." % key)

    # immediately fail with no overriden `get`
    if not hasattr(self.__class__, 'get') and (
      self.__class__ != ModelAdapter):  # pragma: no cover
      ctx = self.__class__.__name__
      raise RuntimeError("ModelAdapter `%s` does not implement `get`,"
                         " and thus cannot be used for reads." % ctx)
    else:
      # grab getter method
      getter = getattr(self.__class__, 'get')

    # flatten key into stringified repr
    joined, flattened = key.flatten(True)
    parent, kind, id = flattened

    # optionally allow adapter to encode key
    encoded = self.encode_key(joined, flattened)

    if not encoded:  # pragma: no cover
      # otherwise, use regular base64 via `AbstractKey`
      encoded = key.urlsafe(joined)

    # pass off to delegated `get`
    try:
      entity = getter((encoded, flattened), **kwargs)
    except NotImplementedError:  # pragma: no cover
      ctx = self.__class__.__name__
      raise RuntimeError("ModelAdapter `%s` does not implement `get`,"
                         " and thus cannot be used for reads." % ctx)
    except RuntimeError:  # pragma: no cover
      raise
    else:
      if entity is None: return  # not found

      if isinstance(entity, dict):  # inflate dict
        entity['key'] = key
        entity = self.registry[kind](_persisted=True, **entity)

      # inflate key + model and return
      key.__persisted__ = True
      return entity

  def _get_multi(self, keys, **kwargs):

    """ Low-level method for retrieving a set of entities via an iterable of
        keys, all in one go.

        :param keys: Iterable of :py:class:`model.Key` instances to retrieve
          from storage.

        :param kwargs: Keyword arguments to pass to the delegated adapter
          method (implementation-specific).

        :raises RuntimeError: If the target :py:class:`adapter.ModelAdapter`
          does not implement ``get_multi()``, which is an ABC-enforced child
          class method. :py:exc:`RuntimeError` and descendents are also
          re-raised from the concrete adapter.

        :returns: Inflated :py:class:`model.Model` instance, corresponding to
            ``key``, or ``None`` if no such entity could be found. """

    from canteen import model

    # immediately fail with no overriden `get`
    if not hasattr(self.__class__, 'get_multi') and (
          self.__class__ != ModelAdapter):  # pragma: no cover
      ctx = self.__class__.__name__
      raise RuntimeError("ModelAdapter `%s` does not implement `get_multi`,"
                         " and thus cannot be used for bulk reads." % ctx)
    else:
      # grab getter method
      getter = getattr(self.__class__, 'get_multi')

    bundles = []
    for key in keys:

      # get key from model, if needed
      if isinstance(key, model.Model): key = key.key

      # flatten key into stringified repr
      joined, flattened = key.flatten(True)

      # optionally allow adapter to encode key
      encoded = self.encode_key(joined, flattened)

      if not encoded:  # pragma: no cover
        # otherwise, use regular base64 via `AbstractKey`
        encoded = key.urlsafe(joined)

      bundles.append((encoded, flattened))  # append to bundles

    # pass off to delegated `get_multi`
    try:
      for entity in getter(bundles, **kwargs):
        yield entity

    except NotImplementedError:  # pragma: no cover
      ctx = self.__class__.__name__
      raise RuntimeError("ModelAdapter `%s` does not implement `get`,"
                         " and thus cannot be used for reads." % ctx)
    except RuntimeError:  # pragma: no cover
      raise

  def _put(self, entity, **kwargs):

    """ Low-level method for persisting an Entity. Collapses and serializes the
        target ``entity`` into native types and delegates to the active
        :py:class:`model.adapter.ModelAdapter` for storage.

        :param entity: Object descendent of :py:class:`model.Model`, suitable
          for storage via the currently-active adapter.

        :raises ValueError: In the case of an unknown or unregistered *kind*.
        :returns: New (or updated) key value for the target ``entity``. """

    # resolve model class
    _model = self.registry.get(entity.kind())
    if not _model:  # pragma: no cover
      raise ValueError('Could not resolve model class "%s".' % entity.kind())

    with entity:  # enter explicit mode

      # validate entity, will raise validation exceptions
      for name, value in entity.to_dict(_all=True).items():
        _model[name].valid(entity)

      # resolve key if we have a zero-y key or key class
      if not entity.key or entity.key is None:
        # build an ID-based key
        ids = self.allocate_ids(_model.__keyclass__, entity.kind())
        entity._set_key(_model.__keyclass__(entity.kind(), ids))

      # flatten key/entity
      joined, flat = entity.key.flatten(True)

    # delegate
    return self.put((
      self.encode_key(joined, flat) or entity.key.urlsafe(joined), flat),
        entity._set_persisted(True), _model, **kwargs)

  def _delete(self, key, **kwargs):

    """ Low-level method for deleting an entity by Key.

        :param key: Target :py:class:`model.Key` to delete.
        :returns: Result of the delete operation. """

    if self.config.get('debug', False):  # pragma: no cover
      self.logging.info("Deleting Key: \"%s\"." % key)

    joined, flat = key.flatten(True)
    return self.delete((
      self.encode_key(joined, flat) or key.urlsafe(joined), flat), **kwargs)

  @classmethod
  def _register(cls, model):

    """ Low-level method for registering a Model class with this adapter's this
        adapter's registry.

        :param model: :py:class:`model.Model` class to register.
        :returns: The ``model`` it was handed (for chainability). """

    cls.registry[model.kind()] = model
    return model

  ## == Class Methods == ##
  @classmethod
  def acquire(cls, name, bases, properties):

    """ Acquire a new/existing copy of this adapter. Available for override by
        child classes to customize the driver acquisition process. Passed an
        identical signature to ``type``, *before* the :py:class:`model.Model`
        class has been fully-built.

        :param name: String name of the new :py:class:`model.Model` class-to-be.
        :param bases: Tuple of base classes for the target :py:class:`Model`.
        :param properties: Property ``dict`` from class definition.

        :returns: The "acquired" adapter object. """

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

    """ Retrieve an entity by :py:class:`model.Key`. Must accept a tuple in the
        format ``(<joined Key repr>, <flattened key>)``. Abstract method that
        **must** be overridden by concrete implementors of
        :py:class:`ModelAdapter`.

        :param key: Target :py:class:`model.Key` to retrieve.
        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`ModelAdapter.get`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover

  @abc.abstractmethod
  def get_multi(cls, keys, **kwargs):  # pragma: no cover

    """ Retrieve multiple entities by :py:class:`model.Key` in one go. Accepts
        an iterable of ``keys``, where each entry is either an instance of
        :py:class:`model.Key` or a tupled pair of ``(encoded, flattened)``,
        produced by the utility method ``key.flatten(True)``.

        :param keys: Iterable of ``keys`` to fetch from underlying storage,
          where each entry is either an instance of :py:class:`model.Key` or
          a tupled pair of ``(encoded, flattened)``, as produced by the utility
          method ``key.flatten(True)``.

        :param kwargs: Keyword arguments (implementation-specific) to pass to
          the underlying driver.

        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`ModelAdapter.get`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover

  @abc.abstractmethod
  def put(cls, key, entity, model, **kwargs):  # pragma: no cover

    """ Persist an entity in storage. Must accept a :py:class:`model.Key`, which
        may not have an ID, in which case one is allocated. The entity and
        :py:class:`model.Model` class are also passed in.

        This method is abstract and **must** be overridden by concrete
        implementors of :py:class:`ModelAdapter`.

        :param key: Potentially-empty :py:class:`model.Key` for the new entity.
        :param entity: Object :py:class:`model.Model` to persist in storage.
        :param model: :py:class:`model.Model` class for target ``entity``.
        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`ModelAdapter.put`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover

  @abc.abstractmethod
  def delete(cls, key, **kwargs):  # pragma: no cover

    """ Delete an entity by :py:class:`model.Key`. Must accept a target
        ``key``, whose associated entity will be deleted.

        This method is abstract and **must** be overridden by concrete
        implementors of :py:class:`ModelAdapter`.

        :param key: Target :py:class:`model.Key` to delete.
        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`ModelAdapter.delete`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover

  @abc.abstractmethod
  def allocate_ids(cls, key_cls, kind, count=1, **kwargs):  # pragma: no cover

    """ Allocate new :py:class:`model.Key` IDs for ``kind`` up to ``count``.
        This method is abstract and **must** be overridden by concrete
        implementors of :py:class:`ModelAdapter`.

        :param key_class: :py:class:`model.Key` class for provisioned IDs.
        :param kind: String ``kind`` name from :py:class:`model.Model` class.
        :param count: Count of IDs to provision, defaults to ``1``.
        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`ModelAdapter.allocate_ids`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover

  @classmethod
  def encode_key(cls, key, joined, flattened):

    """ Encode a :py:class:`model.Key` for storage. This method is abstract and
        *should* be overridden by concrete implementors of
        :py:class:`ModelAdapter`.

        In the case that a :py:class:`ModelAdapter` wishes to defer to the
        default encoder (:py:mod:`base64`), it can return ``False``.

        :param key: Target :py:class:`model.Key` to encode.
        :param joined: Joined/stringified key.
        :param flattened: Flattened ``tuple`` (raw) key.
        :returns: The encoded :py:class:`model.Key`, or ``False`` to
              yield to the default encoder. """

    # by default, yield to key b64 builtin encoding
    return False  # pragma: no cover


# noinspection PyAbstractClass
class IndexedModelAdapter(ModelAdapter):

  """ Abstract base class for model adapters that support additional indexing
      APIs. """

  # magic prefixes
  _key_prefix = '__key__'
  _kind_prefix = '__kind__'
  _group_prefix = '__group__'
  _index_prefix = '__index__'
  _reverse_prefix = '__reverse__'


  class Indexer(object):

    """ Holds methods for indexing and handling index data types. """

    _magic = {
      'key': 0x1,  # magic ID for `model.Key` references
      'date': 0x2,  # magic ID for `datetime.date` instances
      'time': 0x3,  # magic ID for `datetime.time` instances
      'datetime': 0x4}  # magic ID for `datetime.datetime` instances

    @classmethod
    def convert_key(cls, key):

      """ Convert a :py:class:`model.Key` to an indexable value.

          :param key: Target :py:class:`model.Key` to convert.

          :returns: Tupled ``(<magic key code>, <flattened key>)``, suitable for
            adding to the index. """

      # flatten and return key structure with magic
      joined, flattened = key.flatten(True)
      return cls._magic['key'], map(lambda x: x is not None, flattened)

    @classmethod
    def convert_date(cls, _date):

      """ Convert a Python ``date`` to an indexable value.

          :param date: Python ``date`` to convert.

          :returns: Tupled ``(<magic date code>, <flattened date>)`` to add to
            the index. """

      # convert to ISO format, return date with magic
      return cls._magic['date'], float(time.mktime(_date.timetuple()))

    @classmethod
    def convert_time(cls, _time):

      """ Convert a Python ``time`` to an indexable value.

          :param _time: Python ``time`` to convert.

          :returns: Tupled ``(<magic time code>, <flattened time>)``, suitable
            for addition to the index. """

      # convert to ISO format, return time with magic
      return cls._magic['time'], _time.isoformat()

    @classmethod
    def convert_datetime(cls, _datetime):

      """ Convert a Python ``datetime`` to an indexable value.

          :param _datetime: Python ``datetime`` to convert.

          :returns: Tupled ``(<magic time code>, <flattened datetime>)``,
            suitable for addition to the index. """

      # convert to integer, return datetime with magic
      return cls._magic['datetime'], float(time.mktime(_datetime.timetuple()))

  @decorators.classproperty
  def _index_basetypes(cls):

    """ Map basetypes to indexer routines.

        :returns: Default basetype ``dict``. """

    from canteen import model

    return {

      # -- basetypes -- #
      int: cls.serializer.dumps,
      bool: cls.serializer.dumps,
      long: cls.serializer.dumps,
      float: cls.serializer.dumps,
      basestring: cls.serializer.dumps,

      # -- model/key types -- #
      model.Key: cls.Indexer.convert_key,

      # -- date/time types -- #
      datetime.date: cls.Indexer.convert_date,
      datetime.time: cls.Indexer.convert_time,
      datetime.datetime: cls.Indexer.convert_datetime

    }

  def _put(self, entity, **kwargs):  # pragma: no cover

    """ Hook to trigger index writes for a given entity. Defers up the chain to
        :py:class:`ModelAdapter` after generating (and potentially writing) a
        set of indexes from the target ``entity``.

        :param entity: Entity :py:class:`model.Model` to persist.

        :returns: Resulting :py:class:`model.Key` from write operation. """

    # small optimization - with a deterministic key, we can parrellelize
    # index writes (assuming async is supported in the underlying driver)

    _indexed_properties = self._pluck_indexed(entity)

    # delegate write up the chain
    written_key = super(IndexedModelAdapter, self)._put(entity, **kwargs)

    # proxy to `generate_indexes` and write indexes
    if not _indexed_properties:  # pragma: no cover
      origin, meta = self.generate_indexes(entity.key)
      property_map = {}
    else:
      origin, meta, property_map = (
        self.generate_indexes(entity.key, _indexed_properties))

    self.write_indexes((origin, meta, property_map), **kwargs)
    return written_key  # delegate up the chain for entity write

  def _delete(self, key, **kwargs):

    """ Hook to trigger index cleanup for a given key. Defers up the chain to
        :py:class:`ModelAdapter` after generating a set of indexes to clean for
        the target ``key``.

        :param key: Target :py:class:`model.Key` to delete.

        :returns: Result of delete operation. """

    # generate meta indexes only, then clean
    self.clean_indexes(self.generate_indexes(key))

    # delegate delete up the chain
    return super(IndexedModelAdapter, self)._delete(key)

  @staticmethod
  def _pluck_indexed(entity, context=None, _map=None):

    """ Zip and pluck only properties that should be indexed. Simply returns a
        set of property descriptors, mapped to ehtir names in a ``dict``, if
        they are marked as needing to be indexed.

        :param entity: Target entity to produce indexes for.

        :returns: Map ``dict`` of properties to index. """

    from canteen import model

    _map = _map or {}
    _edict = entity if isinstance(entity, dict) else entity.to_dict(
      convert_datetime=False)

    # grab only properties enabled for indexing
    is_indexed = lambda x: entity.__class__.__dict__[x[0]].indexed
    for k, v in filter(is_indexed, _edict.items()):
      prop = entity.__class__.__dict__[k]

      if isinstance(prop.basetype, type) and (
              issubclass(prop.basetype, model.Model) and (
              prop.options.get('embedded'))):  # pragma: no cover
        #_map = IndexedModelAdapter._pluck_indexed(getattr(entity, k), k, _map)
        continue

      else:
        # attach property name, property class, value
        _map['.'.join((context, k)) if context else k] = (prop, v)

    return _map

  def _execute_query(self, query):

    """ Execute a ``query.Query`` object, returning results that match the
        search terms specified in ``query`` and the attached
        ``query.QueryOptions`` object.

        :param query: ``query.Query`` to execute via the local adapter.

        :returns: Query results, if any. """

    return self.execute_query(*(
      query.kind, (query.filters, query.sorts), query.options))

  @classmethod
  def generate_indexes(cls, key, properties=None):

    """ Generate a set of indexes that should be written to with associated
        values.

        :param key: Target :py:class:`model.Key` to index.
        :param properties: Entity :py:class:`model.Model` property values to
          index.

        :returns: Tupled set of ``(encoded, meta, property)``, where ``meta``
          and ``property`` are indexes to be written in each category. """

    if key is None and not properties:  # pragma: no cover
      raise TypeError('Must pass at least `key` or `properties'
                      ' to `generate_indexes`.')

    _property_indexes, _meta_indexes = [], []

    if key is not None:

      # provision vars, generate meta indexes
      # meta indexes look like:
      #  (`__key__`,), target
      #  (`__kind__`, kind), target

      encoded_key = cls.encode_key(*key.flatten(True)) or key.urlsafe()
      _meta_indexes.append((cls._key_prefix,))
      _meta_indexes.append((cls._kind_prefix, key.kind))  # map kind

      # consider ancestry
      if not key.parent:

        # generate group indexes in the case of a nonvoid parent
        # group indexes look like:
        #  (`<group-key>`,), target

        _meta_indexes.append((cls._group_prefix,))

      else:

        # generate group prefix for root
        # root indexes look like:
        #  `__group__`, trimmed-target-root-key

        # append keyparent-based group prefix
        root_key = (i for i in key.ancestry).next()

        # encode root key
        encoded_root_key = (
          cls.encode_key(*root_key.flatten(True)) or root_key.urlsafe())
        _meta_indexes.append((cls._group_prefix, encoded_root_key))

    # add property index entries
    if properties is not None:

      # we're applying writes
      for k, v in properties.items():

        # extract property class and value
        prop, value = v

        # consider repeated properties
        if not prop.repeated or not isinstance(value, (
          tuple, list, set, frozenset)):
          value = [value]

        # generate property index entries for values
        # property value indexes look like:
        #  `__index__::kind::property::encoded_value`, target

        # and the internal representation looks like:
        #  `(value_encoder_callable, (index_prefix, kind, propname, value))`

        # iterate through property values
        for x in value:
          context = (cls._index_prefix, key.kind, k, x)
          _property_indexes.append((
            cls._index_basetypes.get(prop.basetype, basestring), context))

        continue

    else:
      # we're cleaning indexes
      return encoded_key, _meta_indexes
    return encoded_key, _meta_indexes, _property_indexes

  @abc.abstractmethod
  def write_indexes(cls, writes, **kwargs):

    """ Write a batch of index updates generated earlier via
        :py:meth:`generate_indexes`. This method is abstract and **must** be
        overridden by concrete implementors of :py:class:`IndexedModelAdapter`.

        :param writes: Batch of index writes to commit, generated via
          :py:meth:`generate_indexes`.

        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`IndexedModelAdapter.write_indexes`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover

  @abc.abstractmethod
  def clean_indexes(cls, key, **kwargs):

    """ Clean indexes and index entries matching a particular
        :py:class:`model.Key`. This method is abstract and **must** be
        overridden by concrete implementors of :py:class:`IndexedModelAdapter`.

        :param key: Target :py:class:`model.Key` to clean indexes for.
        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`IndexedModelAdapter.clean_indexes`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover

  @abc.abstractmethod
  def execute_query(cls, kind, spec, options, **kwargs):

    """ Execute a query, specified by ``spec``, across one (or multiple) indexed
        properties.

        :param spec: Object specification (:py:class:`model.Query`) specifying
          the query to satisfy.

        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`IndexedModelAdapter.execute_query`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover


class GraphModelAdapter(IndexedModelAdapter):

  """ Abstract base class for model adapters that support Graph-style paradigms
      for data storage. """

  # graph/vertex/edge prefixes
  _edge_prefix = '__edge__'
  _graph_prefix = '__graph__'
  _vertex_prefix = '__vertex__'

  # universal tokens
  _neighbors_token = 'neighbors'

  # directed tokens
  _in_token = 'in'
  _out_token = 'out'
  _directed_token = 'directed'

  # undirected tokens
  _peers_token = 'peers'
  _undirected_token = 'undirected'


  class Indexer(IndexedModelAdapter.Indexer):

    """ Adds Graph-specific ``Indexer`` routines and constants. """

    _magic = {
      'key': 0x1,  # magic ID for `model.Key` references
      'date': 0x2,  # magic ID for `datetime.date` instances
      'time': 0x3,  # magic ID for `datetime.time` instances
      'datetime': 0x4,  # magic ID for `datetime.datetime` instances
      'vertex': 0x5,  # magic ID for `Vertex` `model.Key` references
      'edge': 0x6}  # magic ID for `Edge` `model.Key` references

    @classmethod
    def convert_key(cls, key):

      """ Convert a :py:class:`model.Key` to an indexable value, considering
          ``Vertex`` and ``Edge`` keys as well.

          :param key: Target :py:class:`model.Key` to convert.

          :returns: Tupled ``(<magic key code>, <flattened key>)``, suitable for
            adding to the index. """

      from canteen import model

      if isinstance(key, basestring):
        # expand from urlsafe
        # @TODO(sgammon): this is disgusting what was i thinking
        # @TODO(sgammon): come up with a proper native repr for a key
        key = model.Key(urlsafe=key)  # pragma: no cover

      joined, flattened = key.flatten(True)
      sanitized = map(lambda x: x is not None, flattened)

      _GRAPH_KEYS = (model.Vertex.__keyclass__, model.Edge.__keyclass__)

      _key = 'key'
      if hasattr(key, '__vertex__') and key.__vertex__:
        _key = 'vertex'  # pragma: no cover
      elif hasattr(key, '__edge__') and key.__edge__:
        _key = 'edge'  # pragma: no cover
      return (cls._magic[_key], key.urlsafe())

  @decorators.classproperty
  def _index_basetypes(self):

    """ Map basetypes to indexer routines, with support for graph-specialized
        key types (``VertexKey`` and ``EdgeKey``).

        :returns: Default basetype ``dict``. """

    from canteen import model
    types = super(GraphModelAdapter, self)._index_basetypes

    types.update({
      # -- graph key types -- #
      model.Key: self.Indexer.convert_key,
      model.EdgeKey: self.Indexer.convert_key,
      model.VertexKey: self.Indexer.convert_key})
    return types

  @staticmethod
  def _pluck_indexed(entity):

    """ Override the indexed property scanner to ignore ``Edge``-related auto-
        injected properties.

        :param entity: Target entity to produce indexes for.

        :returns: Map ``dict`` of properties to index. """

    _map = IndexedModelAdapter._pluck_indexed(entity)

    # don't index graph properties - they are resovled via graph indexes
    if hasattr(entity.__class__, '__edge__') and entity.__class__.__edge__:
      if 'peers' in _map: del _map['peers']
      if 'target' in _map: del _map['target']
      if 'source' in _map: del _map['source']
    return _map

  def _put(self, entity, **kwargs):

    """ Override to enable ``graph``-specific indexes (for stored ``Vertex`` and
        ``Edge`` objects/keys).

        :param entity: Entity :py:class:`model.Model` to persist.

        :returns: Resulting :py:class:`model.Key` from write operation. """

    # small optimization - with a deterministic key, we can parrellelize
    # index writes (assuming async is supported in the underlying driver)

    _indexed_properties = self._pluck_indexed(entity)

    # delegate write up the chain
    written_key = super(IndexedModelAdapter, self)._put(entity, **kwargs)

    # proxy to `generate_indexes` and write indexes
    origin, meta, properties, graph = (
      self.generate_indexes(entity.key, entity, _indexed_properties))

    self.write_indexes((origin, meta, properties), graph, **kwargs)
    return written_key  # delegate up the chain for entity write

  @classmethod
  def generate_indexes(cls, key, entity=None, properties=None):

    """ Generate a set of indexes that should be written to with associated
        values, considering that some ``key`` values may be ``VertexKey`` or
        ``EdgeKey`` instances.

        :param key: Target :py:class:`model.Key`, :py:class:`VertexKey` or
          :py:class:`EdgeKey` to index.

        :param entity: :py:class:`Model` entity to be stored. Defaults to
          ``None``, in which case we're cleaning indexes and don't have access
          to the original entity - just the key.

        :param properties: Entity :py:class:`model.Model` property values to
          index.

        :raises TypeError: If neither a ``key`` or ``properties`` are passed,
          since we can't generate anything without at least one or the other.

        :returns: Tupled set of ``(encoded, meta, property, graph)``, where
          ``meta`` and ``property`` are indexes to be written in each category
           and ``graph`` is a bundle of special indexes for ``Vertex`` and
           ``Edge`` keys. """

    from .. import Key, Model

    if key is None and not properties:  # pragma: no cover
      raise TypeError('Must pass at least `key` or `properties'
                      ' to `generate_indexes`.')

    if not (entity is None or isinstance(entity, Model)):  # pragma: no cover
      raise TypeError('Must pass either `None` or a `Model`'
                      ' for the `entity` parameter to `generate_indexes`.'
                      ' Instead, got: "%s".' % entity)

    from .. import VertexKey, EdgeKey
    _super = super(GraphModelAdapter, cls).generate_indexes

    # initialize graph indexes
    graph = []

    if key and properties is None:
      # we're probably cleaning indexes
      encoded, meta = _super(key)

    else:
      # defer upwards for regular indexes
      encoded, meta, properties = _super(key, properties)

    if key:
      # vertex keys
      if isinstance(key, VertexKey):
        graph.append((cls._vertex_prefix,))

      # edge keys
      elif isinstance(key, EdgeKey):

        # main edge index
        graph.append((cls._edge_prefix,))

        if entity:
          # extract spec @TODO(sgammon): make specs not suck
          spec = entity.__spec__

          # directed/undirected index
          graph.append((cls._edge_prefix, cls._directed_token if (
            spec.directed) else cls._undirected_token))

          # directed indexes
          if spec.directed:

            for target in entity.target:

              if isinstance(target, Key) and not (
                  isinstance(target, VertexKey)):  # pragma: no cover
                # @TODO(sgammon): unambiguous graph keys
                target = VertexKey.from_urlsafe(target.urlsafe())

              # __graph__::<source>::out => edge
              graph.append((entity.source, cls._out_token, entity.key))

              # __graph__::<target>::in => edge
              graph.append((target, cls._in_token, entity.key))

              # __graph__::<source>::neighbors => target
              graph.append((entity.source, cls._neighbors_token, target))

              # __graph__::<target>::neighbors => source
              graph.append((target, cls._neighbors_token, entity.source))

          # undirected indexes
          else:

            _indexed_pairs = set()
            for o, source in enumerate(entity.peers):

              if isinstance(source, Key) and not (
                  isinstance(source, VertexKey)):  # pragma: no cover
                # @TODO(sgammon): unambiguous graph keys
                source = VertexKey.from_urlsafe(source.urlsafe())

              for i, target in enumerate(entity.peers):

                if isinstance(target, Key) and not (
                    isinstance(target, VertexKey)):  # pragma: no cover
                  # @TODO(sgammon): unambiguous graph keys
                  target = VertexKey.from_urlsafe(target.urlsafe())

                # skip if it's the same object in the pair
                if o == i: continue  # pragma: no cover

                # skip if we've already indexed the two, since we're undirected
                # and one iteration past either will work for both
                if (source, target) in _indexed_pairs or (
                    (target, source) in _indexed_pairs):  # pragma: no cover
                  continue

                # __graph__::<source>::peers => edge
                graph.append((source, cls._peers_token, entity.key))

                # __graph__::<target>::peers => edge
                graph.append((target, cls._peers_token, entity.key))

                # __graph__::<source>::neighbors => target
                graph.append((source, cls._neighbors_token, target))

                # __graph__::<target>::neighbors => source
                graph.append((target, cls._neighbors_token, source))

    if key and properties is None:
      return encoded, meta, tuple(graph)
    return encoded, meta, properties, tuple(graph)

  @abc.abstractmethod
  def write_indexes(cls, writes, graph, **kwargs):

    """ Write a batch of index updates generated earlier via
        :py:meth:`generate_indexes`. This method is abstract and **must** be
        overridden by concrete implementors of :py:class:`IndexedModelAdapter`.

        :param writes: Batch of index writes to commit, generated via
          :py:meth:`generate_indexes`.

        :param graph: Batch of graph-related storage updates for indexes related
          to ``Edge`` and ``Vertex`` objects.

        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`GraphModelAdapter.write_indexes`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover

  @abc.abstractmethod
  def clean_indexes(cls, key, graph, **kwargs):

    """ Clean indexes and index entries matching a particular
        :py:class:`model.Key`. This method is abstract and **must** be
        overridden by concrete implementors of :py:class:`IndexedModelAdapter`.

        :param key: Target :py:class:`model.Key` to clean indexes for.
        :raises: :py:exc:`NotImplementedError`, as this method is abstract. """

    raise NotImplementedError('`IndexedModelAdapter.clean_indexes`'
                              ' is abstract and may not be'
                              ' called directly.')  # pragma: no cover


class DirectedGraphAdapter(GraphModelAdapter):

  """ Abstract base class for model adpaters that support directed-graph-type
      models. """


# noinspection PyAttributeOutsideInit
class Mixin(object):

  """ Abstract parent for detecting and registering `Mixin` classes. """

  __slots__ = tuple()

  class __metaclass__(type):

    """ Local `Mixin` metaclass for registering encountered `Mixin`(s). """

    ## == Mixin Registry == ##
    _compound = {}
    _mixin_lookup = set()
    _key_mixin_registry = {}
    _model_mixin_registry = {}
    _vertex_mixin_registry = {}
    _edge_mixin_registry = {}

    def __new__(cls, name, bases, properties):

      """ Factory a new registered :py:class:`Mixin`. Registers the target
          ``Mixin`` in :py:attr:`Mixin.__metaclass__._mixin_lookup`, and
          extends compound class at :py:attr:`Mixin.__metaclass__._compound`.

          :param name: Name of ``Mixin`` class to construct.
          :param bases: Class bases of ``Mixin`` class to construct.
          :param properties: Mapping ``dict`` of class properties.
          :raises RuntimeError: For invalid inheritance between mixin bases.

          :returns: Constructed ``Mixin`` class. """

      # apply local metaclass to factoried concrete children
      klass = super(cls, cls).__new__(cls, name, bases, properties)

      # register mixin if it's not a concrete parent and is unregistered
      if name not in frozenset(_core_mixin_classes) and (
        name not in cls._mixin_lookup):

        # add to each registry that the mixin supports
        for base in bases:

          ## add mixin to parent registry
          base.__registry__[name] = klass

        # add to global mixin lookup to prevent double loading
        cls._mixin_lookup.add(name)

        # see if we already have a compound class (mixins loaded after models)
        if Mixin._compound.get(cls):

          ## extend class dict if we already have one
          Mixin._compound.__dict__.update(*(
            dict(cls.__dict__.items())))  # pragma: no cover

      return klass

    def __repr__(cls):

      """ Generate a string representation of a `Mixin` subclass.

          :returns: String *repr* for ``Mixin`` class. """

      return "Mixin(%s.%s)" % (cls.__module__, cls.__name__)

  internals = __metaclass__

  @decorators.classproperty
  def methods(cls):

    """ Recursively return all available ``Mixin`` methods.

        :yields: Each method in each ``Mixin``. """

    for component in cls.components:
      for method, func in component.__dict__.items():
        yield method, func

  @decorators.classproperty
  def compound(cls):

    """ Generate a compound ``Mixin`` class. Builds a new class, composed of all
        available methods on attached mixins.

        :returns: Factoried compound ``Mixin`` class. """

    global CompoundKey, CompoundModel, CompoundVertex, CompoundEdge

    if isinstance(cls.__compound__, basestring):

      # if we've never generated a `CompoundModel`, regenerate...
      cls.__compound__ = cls.internals._compound[cls] = type(*(
        cls.__compound__,
        (cls, object),
        dict([
          ('__origin__', cls),
          ('__slots__', tuple()),
        ] + [(k, v) for k, v in cls.methods])))

      if cls.__compound__.__name__ == 'CompoundKey':
        CompoundKey = cls.__compound__
      elif cls.__compound__.__name__ == 'CompoundModel':
        CompoundModel = cls.__compound__
      elif cls.__compound__.__name__ == 'CompoundVertex':
        CompoundVertex = cls.__compound__
      elif cls.__compound__.__name__ == 'CompoundEdge':
        CompoundEdge = cls.__compound__

    return cls.__compound__

  @decorators.classproperty
  def components(cls):

    """ Return registered ``Mixin`` classes for the current ``cls``.

        :yields: Each mixin in the registry. """

    for mixin in cls.__registry__.itervalues(): yield mixin


class KeyMixin(Mixin):

  """ Allows injection of attributes into `Key`. """

  __slots__ = tuple()
  __compound__ = 'CompoundKey'
  __registry__ = Mixin._key_mixin_registry


class ModelMixin(Mixin):

  """ Allows injection of attributes into `Model`. """

  __slots__ = tuple()
  __compound__ = 'CompoundModel'
  __registry__ = Mixin._model_mixin_registry


class VertexMixin(Mixin):

  """ Allows injection of attributes into `Vertex`. """

  __slots__ = tuple()
  __compound__ = 'CompoundVertex'
  __registry__ = Mixin._vertex_mixin_registry


class EdgeMixin(Mixin):

  """ Allows injection of attributes into `Edge`. """

  __slots__ = tuple()
  __compound__ = 'CompoundEdge'
  __registry__ = Mixin._edge_mixin_registry
