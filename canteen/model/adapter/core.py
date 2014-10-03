# -*- coding: utf-8 -*-

"""

  core model adapters
  ~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import json
import base64
import datetime
import collections

# mixin adapters
from .abstract import (KeyMixin,
                       EdgeMixin,
                       ModelMixin,
                       VertexMixin,
                       IndexedModelAdapter)


class AdaptedKey(KeyMixin):

  """ Provides bridged methods between `model.Key` and the Adapter API. """

  ## = Public Methods = ##
  def get(self, adapter=None):

    """ Retrieve a previously-constructed key from available persistence
        mechanisms. """

    if adapter:  # pragma: no cover
      return adapter._get(self)
    return self.__adapter__._get(self)

  def delete(self, adapter=None):

    """ Delete a previously-constructed key from available persistence
        mechanisms. """

    if adapter: return adapter._delete(self)  # overridden adapter
    if self.__owner__:  # pragma: no cover
      # if possible, delegate to owner model
      return self.__owner__.__adapter__._delete(self)
    return self.__class__.__adapter__._delete(self)  # pragma: no cover

  def flatten(self, join=False):

    """ Flatten this Key into a basic structure suitable for transport or
        storage.

        :param join:
        :returns: """

    from canteen import model

    flat = []
    for element in (getattr(self, i) for i in reversed(self.__schema__)):
      if not isinstance(element, model.Key):
        flat.append(element)
      else:
        flat.append(element.flatten(join))

    flat = tuple(flat)
    if join:
      return self.__class__.__separator__.join([
        u'' if i is None else unicode(i) for i in (
          map(lambda x: x[0] if isinstance(x, tuple) else x, flat))]), flat
    return flat

  def urlsafe(self, joined=None):

    """ Generate an encoded version of this Key, suitable for use in URLs.

        :param joined:
        :returns: """

    if not joined: joined, flat = self.flatten(True)
    return base64.b64encode(joined)

  ## = Class Methods = ##
  @classmethod
  def from_raw(cls, encoded, **kwargs):

    """ Inflate a Key from a raw, internal representation.

        :param encoded:
        :param kwargs:
        :returns: """

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
                     parent=last_key or None,
                     _persisted=kwargs.get('_persisted', False))
    return cls(*encoded,
                parent=last_key or None,
                _persisted=kwargs.get('_persisted', False))

  @classmethod
  def from_urlsafe(cls, encoded, _persisted=False):

    """ Inflate a Key from a URL-encoded representation.

        :param encoded:
        :param _persisted:
        :returns: """

    return cls.from_raw(base64.b64decode(encoded), _persisted=_persisted)


class AdaptedModel(ModelMixin):

  """ Provides bridged methods between `model.Model` and the Adapter API. """

  ## = Public Class Methods = ##
  @classmethod
  def get(cls, key=None, name=None, adapter=None, **kwargs):

    """ Retrieve a persisted version of this model via the current model
        adapter.

        :param key:
        :param name:
        :param kwargs:

        :raises:
        :returns: """

    if not key and not name:
      raise ValueError('Must pass either a Key or'
                       ' key name into'
                       ' `%s.get`.' % cls.kind())  # pragma: no cover

    adapter = adapter or cls.__adapter__

    if name:
      # if we're passed a name, construct a key with the local kind
      return adapter._get(cls.__keyclass__(cls.kind(), name), **kwargs)
    if isinstance(key, basestring):
      # assume URL-encoded key, this is user-facing
      key = cls.__keyclass__.from_urlsafe(key)
    elif isinstance(key, (list, tuple)):
      key = cls.__keyclass__(*key)  # an ordered partslist is fine too
    return adapter._get(key, **kwargs)

  @classmethod
  def get_multi(cls, keys=None, adapter=None, **kwargs):

    """ Retrieve multiple entities from underlying storage in one-go, as if
        they were retrieved individually via ``get``, but giving the engine
        knowledge and control of what we're doing, which is fetching multiple
        things.

        :param keys: Iterable of :py:class:`model.Key` instances to fetch from
          underlying storage.

        :param adapter: Adapter to use in place of the ``cls`` ``Model``
          subtype's default adapter, if any. ``None`` uses the default adapter
          resolution flow, which is the default.

        :param kwargs: Keyword arguments (implementation-specific) to be passed
          to the underlying driver.

        :return: Iterable of object results, with order preserved from ``keys``
          requested for fetch. """

    # resolve adapter, delegate to `get_multi`
    for key, result in zip(keys, (adapter or cls.__adapter__)._get_multi(
          keys, **kwargs)):
      yield result

  @classmethod
  def query(cls, *args, **kwargs):

    """ Start building a new `model.Query` object, if the underlying adapter
        implements `IndexedModelAdapter`.

        :param args:
        :param kwargs:

        :raises:
        :raises:
        :returns: """

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
                             ' arbitrary objects.'
                             ' Got: "%s".' % arg)  # pragma: no cover

      return query.Query(cls,
                         filters=filters,
                         sorts=sorts,
                         adapter=kwargs.get('adapter'),
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

    """ Persist this entity via the current model adapter.

        :param adapter:
        :param kwargs:
        :returns: """

    # allow adapter override
    if not adapter: adapter = self.__class__.__adapter__
    return adapter._put(self, **kwargs)

  def delete(self, adapter=None, **kwargs):

    """ Discard any primary or index-based data linked to this Key.

        :param adapter:
        :param kwargs:
        :returns: """

    # allow adapter override
    if not adapter: adapter = self.__class__.__adapter__
    return adapter._delete(self.__key__, **kwargs)


class AdaptedVertex(VertexMixin):

  """ Provides graph-oriented methods for ``Vertex`` objects. """

  __graph__ = __vertex__ = True  # mark as graph model and vertex

  def edges(self, tails=None, AND=None, OR=None, **kwargs):

    """ Retrieve edges for the current ``Vertex``.

        :param type:
        :param tails:
        :param heads:
        :param kwargs:

        :raises:
        :returns: """

    from canteen.model.query import EdgeFilter
    return self.query(**kwargs).filter(EdgeFilter(self.key, tails, **{
        'AND': AND, 'OR': OR}))

  def neighbors(self, tails=None, AND=None, OR=None, **kwargs):

    """ Retrieve neighbors (peered edges) for the current ``Vertex``.

        :param type:
        :param tails:
        :param kwargs:

        :raises:
        :returns: """

    from canteen.model.query import EdgeFilter
    return self.query(**kwargs).filter(EdgeFilter(self.key, tails, **{
        'AND': AND, 'OR': OR, 'type': EdgeFilter.NEIGHBORS}))


class AdaptedEdge(EdgeMixin):

  """ Provides graph-oriented methods for ``Edge objects``. """

  __graph__ = __edge__ = True  # mark as graph model and vertex


class DictMixin(ModelMixin):

  """ Provides `to_dict`-type methods for first-class Model API classes. """

  def update(self, mapping=None, **kwargs):

    """ Update properties on this model via a merged dict of mapping + kwargs.

        :param mapping:
        :param kwargs:
        :returns: """

    mapping = mapping or {}
    if kwargs: mapping.update(kwargs)
    map(lambda x: setattr(self, x[0], x[1]), mapping.items())
    return self

  def to_dict(self, exclude=tuple(), include=tuple(),
              filter=None, map=None, _all=False,
              filter_fn=filter, map_fn=map,
              convert_keys=True, convert_models=True, convert_datetime=True):

    """ Export this Entity as a dictionary, excluding/including/ filtering/
        mapping as we go.

        :param exclude:
        :param include:
        :param filter:
        :param map:
        :param _all:
        :param filter_fn:
        :param map_fn:
        :param convert_keys:
        :param convert_models:

        :raises:
        :returns: """

    from canteen import model

    dictionary = {}  # return dictionary
    _default_include = False  # flag for including properties unset

    # explicit mode implies returning all properties raw
    if not _all: _all = self.__explicit__

    if not include:
      include = self.__lookup__  # default include list is model properties
      _default_include = True  # mark flag that we used the default

    if not map:
      map = lambda x: x  # substitute no map with a passthrough
      _default_map = True

    # substitute no filter with a passthrough
    if not filter: filter = lambda x: True


    # freeze our comparison sets
    exclude, include = frozenset(exclude), frozenset(include)

    for name in self.__lookup__:

      # run map fn over (name, value)
      _property_descriptor = self.__class__.__dict__[name]


      # pull with property default
      _prop_default = self.__class__.__dict__[name].default
      name, value = map((name, self._get_value(name, default=_prop_default)))

      # run filter fn over (name, vlaue)
      filtered = filter((name, value))
      if not filtered: continue

      # filter out via exclude/include
      if name in exclude:
        continue
      if not _default_include:
        if name not in include: continue

      if value is _property_descriptor.sentinel:  # property is unset
        # if it matches an item in a custom include list,
        # and/or we don't want all properties...
        if not _all and not ((not _default_include) and name in include):
          continue  # skip if all properties not requested
        else:
          if not self.__explicit__:  # None == sentinel in implicit mode
            dictionary[name] = None
            continue

      _bundle = []

      # validate inner value which may be repeated
      for _val in ((value,) if not isinstance(value, (list, tuple)) else value):

        if isinstance(_val, (model.Model, model.Key)):
          if _property_descriptor.options.get('embedded'):
            if isinstance(_val, model.Key):  # pragma: no cover
              raise RuntimeError('Cannot reference embedded submodel'
                                 ' by key "%s".' % repr(_val))
            _bundle.append(_val.to_dict() if convert_models else _val)
          else:
            if isinstance(_val, model.Model) and not (
                  _val.key):  # pragma: no cover
              raise RuntimeError('Cannot reference non-embedded submodel'
                                 ' "%s" with empty key.' % repr(_val))

            # no embedded status means it should be left as-is
            elif _property_descriptor.options.get('embedded') is None:

              # @TODO(sgammon): decide sensible logic here

              # if mapping is an explicit key, conver it to a string
              if _property_descriptor.basetype is model.Key and (
                    convert_keys):
                _bundle.append(_val.urlsafe())
              else:
                _bundle.append(_val)

            else:  # pragma: no cover
              if isinstance(value, model.Key) and convert_keys:
                _bundle.append(_val.urlsafe())
              elif isinstance(value, model.Model) and convert_models:
                _bundle.append(_val.to_dict())
              else:
                _bundle.append(_val)
        elif isinstance(value, (datetime.date, datetime.datetime)):
          _bundle.append((
            _val if not convert_datetime else _val.isoformat()))
        else:
          _bundle.append(_val)

      if _property_descriptor.repeated:
        dictionary[name] = (
          tuple(_bundle) if isinstance(value, tuple) else _bundle)
      else:
        dictionary[name] = _bundle.pop()
    return dictionary

  @classmethod
  def to_dict_schema(cls):

    """ Convert a model or entity's schema to a dictionary, where keys=>values
        map to properties=>descriptors.

        :returns: """

    schema = {}
    for name in cls.__lookup__:
      schema[name] = getattr(cls, name)
    return schema


class JSONMixin(KeyMixin, ModelMixin):

  """ Provides JSON serialization/deserialization support to `model.Model` and
      `model.Key`. """

  def to_json(self, *args, **kwargs):

    """ Convert an entity to a JSON structure, where keys=>values map to
        properties=>values.

        :param args:
        :param kwargs:
        :returns: """

    return json.dumps(self.to_dict(*args, **kwargs))

  @classmethod
  def from_json(cls, encoded):

    """ Inflate a JSON string into an entity. Expects a dictionary of
        properties=>values.

        :param encoded:
        :returns: """

    return cls(**json.loads(encoded))

  @classmethod
  def to_json_schema(cls, *args, **kwargs):  # pragma: no cover

    """ Convert a model or entity's schema to a dictionary, where keys=>values
        map to JSON Schema representing properties=>descriptors.

        :param args:
        :param kwargs:

        :raises:
        :returns: """

    raise NotImplementedError()  # @TODO: JSON schema support


# msgpack support
try:
  import msgpack
except ImportError as e:  # pragma: no cover
  pass  # no `msgpack` support :(

else:


  class MsgpackMixin(KeyMixin, ModelMixin):

    """ Provides Msgpack serialization/deserialization support to `model.Model`
        and `model.Key`. """

    def to_msgpack(self, *args, **kwargs):

      """ Convert an entity to a Msgpack structure, where keys=>values map to
          properties=>values.

          :param args:
          :param kwargs:

          :returns: """

      return msgpack.dumps(self.to_dict(*args, **kwargs))

    @classmethod
    def from_msgpack(cls, encoded):

      """ Inflate a msgpack payload into an entity. Expects a dictionary of
          properties=>values.

          :param encoded:
          :returns: """

      return cls(**msgpack.unpackb(encoded))

    @classmethod
    def to_msgpack_schema(cls, *args, **kwargs):  # pragma: no cover

      """ Convert a model or entity's schema to a dictionary, where keys=>values
          map to internal symbols representing properties=>descriptors.

          :param args:
          :param kwargs:

          :raises:
          :returns: """

      raise NotImplementedError()  # @TODO: msgpack schema support?
