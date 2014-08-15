# -*- coding: utf-8 -*-

'''

  core model adapters
  ~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import json
import base64
import collections

# mixin adapters
from .abstract import KeyMixin
from .abstract import EdgeMixin
from .abstract import ModelMixin
from .abstract import VertexMixin
from .abstract import IndexedModelAdapter


## Globals
_conditionals = []


## AdaptedKey
class AdaptedKey(KeyMixin):

  ''' Provides bridged methods between `model.Key`
      and the Adapter API. '''

  ## = Public Methods = ##
  def get(self):

    ''' Retrieve a previously-constructed key from
        available persistence mechanisms. '''

    return self.__adapter__._get(self)

  def delete(self):

    ''' Delete a previously-constructed key from
        available persistence mechanisms. '''

    if self.__owner__:
      # if possible, delegate to owner model
      return self.__owner__.__adapter__._delete(self)
    return self.__class__.__adapter__._delete(self)

  def flatten(self, join=False):

    ''' Flatten this Key into a basic structure
        suitable for transport or storage.

        :param join:
        :returns: '''

    flat = tuple((
      i if not isinstance(i, self.__class__) else i.flatten(join)) for i in (
      map(lambda x: getattr(self, x), reversed(self.__schema__))))
    if join:
      return self.__class__.__separator__.join([
        u'' if i is None else unicode(i) for i in (
          map(lambda x: x[0] if isinstance(x, tuple) else x, flat))]), flat
    return flat

  def urlsafe(self, joined=None):

    ''' Generate an encoded version of this Key,
        suitable for use in URLs.

        :param joined:
        :returns: '''

    if not joined: joined, flat = self.flatten(True)
    return base64.b64encode(joined)

  ## = Class Methods = ##
  @classmethod
  def from_raw(cls, encoded, **kwargs):

    ''' Inflate a Key from a raw, internal representation.

        :param encoded:
        :param kwargs:
        :returns: '''

    # if it's still a string, split by separator
    # (probably coming from a DB driver, `urlsafe` does this for us)
    encoded = (collections.deque(encoded.split(cls.__separator__))
               if isinstance(encoded, basestring) else (
                collections.deque(encoded)))

    key, keys = [], []
    if not (len(encoded) > len(cls.__schema__)):
      return cls(*encoded, **kwargs)

    last_key = encoded.popleft()  # we're dealing with ancestry here
    while len(encoded) > 2:
      # recursively decode, removing chunks as we go. extract argset by argset.
      last_key = cls(*(encoded.popleft() for i in (
                     xrange(0, len(cls.__schema__) - 1))),
                     parent=last_key,
                     _persisted=kwargs.get('_persisted', False))
    return cls(*encoded,
                parent=last_key,
                _persisted=kwargs.get('_persisted', False))

  @classmethod
  def from_urlsafe(cls, encoded, _persisted=False):

    ''' Inflate a Key from a URL-encoded representation.

        :param encoded:
        :param _persisted:
        :returns: '''

    return cls.from_raw(base64.b64decode(encoded), _persisted=_persisted)


## AdaptedModel
class AdaptedModel(ModelMixin):

  ''' Provides bridged methods between `model.Model` and
      the Adapter API. '''

  ## = Public Class Methods = ##
  @classmethod
  def get(cls, key=None, name=None, **kwargs):

    ''' Retrieve a persisted version of this model via the current
        model adapter.

        :param key:
        :param name:
        :param kwargs:

        :raises:
        :returns: '''

    if not key and not name:
      raise ValueError('Must pass either a Key or'
                       ' key name into `%s.get`.' % cls.kind())
    if name:
      # if we're passed a name, construct a key with the local kind
      return cls.__adapter__._get(cls.__keyclass__(cls.kind(), name), **kwargs)
    if isinstance(key, basestring):
      # assume URL-encoded key, this is user-facing
      key = cls.__keyclass__.from_urlsafe(key)
    elif isinstance(key, (list, tuple)):
      key = cls.__keyclass__(*key)  # an ordered partslist is fine too
    return cls.__adapter__._get(key, **kwargs)

  @classmethod
  def query(cls, *args, **kwargs):

    ''' Start building a new `model.Query` object, if the underlying
        adapter implements `IndexedModelAdapter`.

        :param args:
        :param kwargs:

        :raises:
        :raises:
        :returns: '''

    # we implement indexer operations
    if isinstance(cls.__adapter__, IndexedModelAdapter):
      from canteen.model import query

      filters, sorts = [], []
      for arg in args:
        if isinstance(arg, query.Filter):
          filters.append(arg)
        elif isinstance(arg, query.Sort):
          sorts.append(arg)
        else:
          raise RuntimeError('Cannot sort or filter based on'
                             ' arbitrary objects. Got: "%s".' % arg)

      return query.Query(cls,
                         filters=filters,
                         sorts=sorts,
                         options=(
                          kwargs['options'] if 'options' in kwargs else (
                            query.QueryOptions(**kwargs))))

    else:  # pragma: no cover
      context = (cls.__adapter__.__class__.__name__, cls.kind())
      raise AttributeError("%s (currently selected for %s) does not"
                           " support indexing, and therefore can't"
                           " work with `model.Query` objects." % context)

  ## = Public Methods = ##
  def put(self, adapter=None, **kwargs):

    ''' Persist this entity via the current
        model adapter.

        :param adapter:
        :param kwargs:
        :returns: '''

    # allow adapter override
    if not adapter: adapter = self.__class__.__adapter__
    return adapter._put(self, **kwargs)

  def delete(self, adapter=None, **kwargs):

    ''' Discard any primary or index-based data
        linked to this Key.

        :param adapter:
        :param kwargs:
        :returns: '''

    # allow adapter override
    if not adapter: adapter = self.__class__.__adapter__
    return adapter._delete(self.__key__, **kwargs)


## AdaptedVertex
class AdaptedVertex(VertexMixin):

  ''' Provides graph-oriented methods for
      ``Vertex`` objects. '''

  __graph__ = __vertex__ = True  # mark as graph model and vertex

  def edges(self, *args, **kwargs):  # pragma: no cover

    ''' Retrieve edges for the current ``Vertex``.

        :param args:
        :param kwargs:

        :raises:
        :returns: '''

    adapter = kwargs.get('adapter', self.__class__.__adapter__)
    return adapter._edges(self, *args, **kwargs)

  def neighbors(self, *args, **kwargs):  # pragma: no cover

    ''' Retrieve neighbors (peered edges) for the
        current ``Vertex``.

        :param args:
        :param kwargs:

        :raises:
        :returns: '''

    adapter = kwargs.get('adapter', self.__class__.__adapter__)
    return adapter._neighbors(self, *args, **kwargs)


## AdaptedEdge
class AdaptedEdge(EdgeMixin):

  ''' Provides graph-oriented methods for ``Edge objects``. '''

  __graph__ = __edge__ = True  # mark as graph model and vertex


## DictMixin
class DictMixin(KeyMixin, ModelMixin):

  ''' Provides `to_dict`-type methods for first-class
      Model API classes. '''

  def update(self, mapping={}, **kwargs):

    ''' Update properties on this model via a merged dict
        of mapping + kwargs.

        :param mapping:
        :param kwargs:
        :returns: '''

    if kwargs: mapping.update(kwargs)
    map(lambda x: setattr(self, x[0], x[1]), mapping.items())
    return self

  def to_dict(self, exclude=tuple(), include=tuple(),
              filter=None, map=None, _all=False,
              filter_fn=filter, map_fn=map):

    ''' Export this Entity as a dictionary, excluding/including/
        filtering/mapping as we go.

        :param exclude:
        :param include:
        :param filter:
        :param map:
        :param _all:
        :param filter_fn:
        :param map_fn:

        :raises:
        :returns: '''

    dictionary = {}  # return dictionary
    _default_include = False  # flag for including properties unset

    # explicit mode implies returning all properties raw
    if not _all: _all = self.__explicit__

    if not include:
      include = self.__lookup__  # default include list is model properties
      _default_include = True  # mark flag that we used the default

    map = map or (lambda x: x)  # substitute no map with a passthrough

    # substitute no filter with a passthrough
    if not filter: filter = lambda x: True

    # freeze our comparison sets
    exclude, include = frozenset(exclude), frozenset(include)

    for name in self.__lookup__:

      # run map fn over (name, value)
      _property_descriptor = self.__class__.__dict__[name]

      # pull with property default
      name, value = map((name, self._get_value(name,
                        default=self.__class__.__dict__[name]._default)))

      # run filter fn over (name, vlaue)
      filtered = filter((name, value))
      if not filtered: continue

      # filter out via exclude/include
      if name in exclude:
        continue
      if not _default_include:
        if name not in include: continue

      if value is _property_descriptor._sentinel:  # property is unset
        # if it matches an item in a custom include list,
        # and/or we don't want all properties...
        if not _all and not ((not _default_include) and name in include):
          continue  # skip if all properties not requested
        else:
          if not self.__explicit__:  # None == sentinel in implicit mode
            value = None
      dictionary[name] = value
    return dictionary

  @classmethod
  def to_dict_schema(cls):

    ''' Convert a model or entity's schema to a dictionary, where
        keys=>values map to properties=>descriptors.

        :returns: '''

    schema = {}
    for name in cls.__lookup__:
      schema[name] = getattr(cls, name)
    return schema


## JSONMixin
class JSONMixin(KeyMixin, ModelMixin):

  ''' Provides JSON serialization/deserialization support to
      `model.Model` and `model.Key`. '''

  def to_json(self, *args, **kwargs):

    ''' Convert an entity to a JSON structure, where keys=>values
        map to properties=>values.

        :param args:
        :param kwargs:
        :returns: '''

    return json.dumps(self.to_dict(*args, **kwargs))

  @classmethod
  def from_json(cls, encoded):

    ''' Inflate a JSON string into an entity. Expects a dictionary
        of properties=>values.

        :param encoded:
        :returns: '''

    return cls(**json.loads(encoded))

  @classmethod
  def to_json_schema(cls, *args, **kwargs):  # pragma: no cover

    ''' Convert a model or entity's schema to a dictionary, where
        keys=>values map to JSON Schema representing
        properties=>descriptors.

        :param args:
        :param kwargs:

        :raises:
        :returns: '''

    raise NotImplementedError()  # @TODO: JSON schema support


# msgpack support
try:
  import msgpack
except ImportError as e:  # pragma: no cover
  pass  # no `msgpack` support :(

else:


  ## MsgpackMixin
  class MsgpackMixin(KeyMixin, ModelMixin):

    ''' Provides Msgpack serialization/deserialization support
        to `model.Model` and `model.Key`. '''

    def to_msgpack(self, *args, **kwargs):

      ''' Convert an entity to a Msgpack structure, where
          keys=>values map to properties=>values.

          :param args:
          :param kwargs:

          :returns: '''

      return msgpack.dumps(self.to_dict(*args, **kwargs))

    @classmethod
    def from_msgpack(cls, encoded):

      ''' Inflate a msgpack payload into an entity. Expects a
          dictionary of properties=>values.

          :param encoded:
          :returns: '''

      return cls(**msgpack.unpackb(encoded))

    @classmethod
    def to_msgpack_schema(cls, *args, **kwargs):  # pragma: no cover

      ''' Convert a model or entity's schema to a dictionary,
          where keys=>values map to internal symbols
          representing properties=>descriptors.

          :param args:
          :param kwargs:

          :raises:
          :returns: '''

      raise NotImplementedError()  # @TODO: msgpack schema support?


  # add to module exports
  _conditionals.append('MsgpackMixin')


__all__ = tuple([
  'AdaptedKey',
  'AdaptedModel',
  'DictMixin',
  'JSONMixin'
] + _conditionals)
