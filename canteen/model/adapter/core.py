# -*- coding: utf-8 -*-

'''

  canteen: core model adapters
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
from .abstract import ModelMixin
from .abstract import IndexedModelAdapter

# canteen util

# @TODO(sgammon): fix this
#from canteen.util import json


## Globals
_conditionals = []


## AdaptedKey
class AdaptedKey(KeyMixin):

  ''' Provides bridged methods between `model.Key` and the Adapter API. '''

  ## = Public Methods = ##
  def get(self):

    ''' Retrieve a previously-constructed key from available persistence mechanisms. '''

    return self.__adapter__._get(self)

  def delete(self):

    ''' Delete a previously-constructed key from available persistence mechanisms. '''

    if self.__owner__:
      return self.__owner__.__adapter__._delete(self)  # if possible, delegate to owner model
    return self.__class__.__adapter__._delete(self)

  def flatten(self, join=False):

    ''' Flatten this Key into a basic structure suitable for transport or storage. '''

    flattened = tuple((i if not isinstance(i, self.__class__) else i.flatten(join)) for i in map(lambda x: getattr(self, x), reversed(self.__schema__)))
    if join: return self.__class__.__separator__.join([u'' if i is None else unicode(i) for i in map(lambda x: x[0] if isinstance(x, tuple) else x, flattened)]), flattened
    return flattened

  def urlsafe(self, joined=None):

    ''' Generate an encoded version of this Key, suitable for use in URLs. '''

    if not joined: joined, flat = self.flatten(True)
    return base64.b64encode(joined)

  ## = Class Methods = ##
  @classmethod
  def from_raw(cls, encoded, **kwargs):

    ''' Inflate a Key from a raw, internal representation. '''

    # if it's still a string, split by separator (probably coming from a DB driver, `urlsafe` does this for us, for instance)
    encoded = collections.deque(encoded.split(cls.__separator__)) if isinstance(encoded, basestring) else collections.deque(encoded)

    key, keys = [], []
    if not (len(encoded) > len(cls.__schema__)):
      return cls(*encoded, **kwargs)

    last_key = encoded.popleft()  # we're dealing with ancestry here
    while len(encoded) > 2:
      # recursively decode, removing chunks as we go. extract argset by argset.
      last_key = cls(*(encoded.popleft() for i in xrange(0, len(cls.__schema__) - 1)), parent=last_key, _persisted=kwargs.get('_persisted', False))
    return cls(*encoded, parent=last_key, _persisted=kwargs.get('_persisted', False))

  @classmethod
  def from_urlsafe(cls, encoded, _persisted=False):

    ''' Inflate a Key from a URL-encoded representation. '''

    return cls.from_raw(base64.b64decode(encoded), _persisted=_persisted)


## AdaptedModel
class AdaptedModel(ModelMixin):

  ''' Provides bridged methods between `model.Model` and the Adapter API. '''

  ## = Public Class Methods = ##
  @classmethod
  def get(cls, key=None, name=None, **kwargs):

    ''' Retrieve a persisted version of this model via the current datastore adapter. '''

    if not key and not name: raise ValueError('Must pass either a Key or key name into `%s.get`.' % cls.kind())
    if name: return cls.__adapter__._get(cls.__keyclass__(cls.kind(), name), **kwargs)  # if we're passed a name, construct a key with the local kind
    if isinstance(key, basestring):
      key = cls.__keyclass__.from_urlsafe(key)  # assume URL-encoded key, this is user-facing
    elif isinstance(key, (list, tuple)):
      key = cls.__keyclass__(*key)  # an ordered partslist is fine too
    return cls.__adapter__._get(key, **kwargs)

  @classmethod
  def query(cls, *args, **kwargs):

    ''' Start building a new `model.Query` object, if the underlying adapter implements `IndexedModelAdapter`. '''

    if isinstance(cls.__adapter__, IndexedModelAdapter):  # we implement indexer operations
      from canteen.model import query

      filters, sorts = [], []
      for arg in args:
        if isinstance(arg, query.Filter):
          filters.append(arg)
        elif isinstance(arg, query.Sort):
          sorts.append(arg)
        else:
          raise RuntimeError('Cannot sort or filter based on arbitrary objects. Got: "%s".' % arg)

      return query.Query(cls, filters=filters, sorts=sorts, options=query.QueryOptions(**kwargs))

    context = (cls.__adapter__.__class__.__name__, cls.kind())
    raise AttributeError("Adapter \"%s\" (currently selected for model \"%s\") does not support indexing, "
               "and therefore can't support `model.Query` objects." % context)

  ## = Public Methods = ##
  def put(self, adapter=None, **kwargs):

    ''' Persist this entity via the current datastore adapter. '''

    if not adapter: adapter = self.__class__.__adapter__  # Allow adapter override
    return adapter._put(self, **kwargs)

  def delete(self, adapter=None, **kwargs):

    ''' Discard any primary or index-based data linked to this Key. '''

    if not adapter: adapter = self.__class__.__adapter__  # Allow adapter override
    return adapter._delete(self.__key__, **kwargs)


## DictMixin
class DictMixin(KeyMixin, ModelMixin):

  ''' Provides `to_dict`-type methods for first-class Model API classes. '''

  def update(self, mapping={}, **kwargs):

    ''' Update properties on this model via a merged dict of mapping + kwargs. '''

    if kwargs: mapping.update(kwargs)
    map(lambda x: setattr(self, x[0], x[1]), mapping.items())
    return self

  def to_dict(self, exclude=tuple(), include=tuple(), filter=None, map=None, _all=False, filter_fn=filter, map_fn=map):

    ''' Export this Entity as a dictionary, excluding/including/filtering/mapping as we go. '''

    dictionary = {}  # return dictionary
    _default_map = False  # flag for default map lambda, so we can exclude only on custom map
    _default_include = False  # flag for including properties unset and explicitly listed in a custom inclusion list

    if not _all: _all = self.__explicit__  # explicit mode implies returning all properties raw

    if not include:
      include = self.__lookup__  # default include list is model properties
      _default_include = True  # mark flag that we used the default

    if not map:
      map = lambda x: x  # substitute no map with a passthrough
      _default_map = True

    if not filter: filter = lambda x: True  # substitute no filter with a passthrough

    # freeze our comparison sets
    exclude, include = frozenset(exclude), frozenset(include)

    for name in self.__lookup__:

      # run map fn over (name, value)
      _property_descriptor = self.__class__.__dict__[name]
      name, value = map((name, self._get_value(name, default=self.__class__.__dict__[name]._default)))  # pull with property default

      # run filter fn over (name, vlaue)
      filtered = filter((name, value))
      if not filtered: continue

      # filter out via exclude/include
      if name in exclude:
        continue
      if not _default_include:
        if name not in include: continue

      if value is _property_descriptor._sentinel:  # property is unset
        if not _all and not ((not _default_include) and name in include):  # if it matches an item in a custom include list, and/or we don't want all properties...
          continue  # skip if all properties not requested
        else:
          if not self.__explicit__:  # None == sentinel in implicit mode
            value = None
      dictionary[name] = value
    return dictionary

  @classmethod
  def to_dict_schema(cls, *args, **kwargs):

    ''' Convert a model or entity's schema to a dictionary, where keys=>values map to properties=>descriptors. '''

    raise NotImplementedError()


## JSONMixin
class JSONMixin(KeyMixin, ModelMixin):

  ''' Provides JSON serialization/deserialization support to `model.Model` and `model.Key`. '''

  def to_json(self, *args, **kwargs):

    ''' Convert an entity to a JSON structure, where keys=>values map to properties=>values. '''

    return json.dumps(self.to_dict(*args, **kwargs))

  @classmethod
  def to_json_schema(cls, *args, **kwargs):

    ''' Convert a model or entity's schema to a dictionary, where keys=>values map to JSON Schema representing properties=>descriptors. '''

    raise NotImplementedError()  # @TODO: JSON schema support


# msgpack support
try:
  import msgpack
except ImportError as e:  # pragma: no cover
  pass  # no `msgpack` support :(

else:

  ## MsgpackMixin
  class MsgpackMixin(KeyMixin, ModelMixin):

    ''' Provides Msgpack serialization/deserialization support to `model.Model` and `model.Key`. '''

    def to_msgpack(cls, *args, **kwargs):

      ''' Convert an entity to a Msgpack structure, where keys=>values map to properties=>values. '''

      raise NotImplementedError()

    @classmethod
    def to_msgpack_schema(cls, *args, **kwargs):

      ''' Convert a model or entity's schema to a dictionary, where keys=>values map to internal symbols representing properties=>descriptors. '''

      raise NotImplementedError()


  # add to module exports
  _conditionals.append('MsgpackMixin')


__all__ = tuple([
  'AdaptedKey',
  'AdaptedModel',
  'DictMixin',
  'JSONMixin'
] + _conditionals)
