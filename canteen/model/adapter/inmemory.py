# -*- coding: utf-8 -*-

'''

  canteen: in-memory model adapter
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import json
import base64

# adapter API
from .abstract import IndexedModelAdapter


## Globals
_init = False
_metadata = {}
_datastore = {}


## InMemoryAdapter
class InMemoryAdapter(IndexedModelAdapter):

  ''' Adapt model classes to RAM. '''

  # key encoding
  _key_encoder = base64.b64encode

  # data compression / encoding
  _data_encoder = json.dumps
  _data_compressor = None

  @classmethod
  def acquire(cls, name, bases, properties):

    ''' Perform first initialization. '''

    global _init
    global _metadata

    # perform first init, if it hasn't been done
    if not _init:
      _init, _metadata = True, {
        'ops': {  # holds count of performed operations
          'get': 0,  # track # of entity get() operations
          'put': 0,  # track # of entity put() operations
          'delete': 0  # track # of entity delete() operations
        },
        'kinds': {},  # holds current count and ID increment pointer for each kind
        'global': {  # holds global metadata, like entity count across kind classes
          'entity_count': 0  # holds global count of all entities
        },
        cls._key_prefix: set([]),  # full, simple indexed set of all keys
        cls._kind_prefix: {},  # maps keys to their kinds
        cls._group_prefix: {},  # maps keys to their entity groups
        cls._index_prefix: {},  # maps property values to keys
        cls._reverse_prefix: {}  # maps keys to indexes they are present in
      }

    # pass up the chain to create a singleton
    return super(InMemoryAdapter, cls).acquire(name, bases, properties)

  @classmethod
  def is_supported(cls):

    ''' Check whether this adapter is supported in the current environment. '''

    # always supported: used in dev/debug, RAM is always there
    return True

  @classmethod
  def get(cls, key, **kwargs):

    ''' Retrieve an entity by Key from Python RAM. '''

    global _metadata

    # key format: tuple(<str encoded key>, <tuple flattened key>)
    encoded, flattened = key
    parent, kind, id = flattened

    # pull from in-memory backend
    entity = _datastore.get(encoded)
    if entity is None: return  # not found

    _metadata['ops']['get'] = _metadata['ops']['get'] + 1

    # construct + inflate entity
    return entity

  @classmethod
  def put(cls, key, entity, model, **kwargs):

    ''' Persist an entity to storage in Python RAM. '''

    global _metadata
    global _datastore

    # encode key and flatten
    encoded, flattened = key

    # perform validation
    with entity:

      if entity.key.kind not in _metadata['kinds']:  # pragma: no cover
        _metadata['kinds'][entity.key.kind] = {
          'id_pointer': 0,  # keep current key ID pointer
          'entity_count': 0  # keep count of seen entities for each kind
        }

      # update count
      _metadata['ops']['put'] = _metadata['ops'].get('put', 0) + 1
      _metadata['global']['entity_count'] = _metadata['global'].get('entity_count', 0) + 1
      kinded_entity_count = _metadata['kinds'][entity.key.kind].get('entity_count', 0)
      _metadata['kinds'][entity.key.kind]['entity_count'] = kinded_entity_count + 1

      # save to datastore
      _datastore[encoded] = entity.to_dict()

    return entity.key

  @classmethod
  def delete(cls, key, **kwargs):

    ''' Delete an entity by Key from memory. '''

    global _metadata
    global _datastore

    # extract key
    if not isinstance(key, tuple):  # pragma: no cover
      encoded, flattened = key.flatten(True)
    else:
      encoded, flattened = key

    # extract key parts
    parent, kind, id = flattened

    # if we have the key...
    if encoded in _metadata[cls._key_prefix]:
      try:
        del _datastore[encoded]  # delete from datastore

      except KeyError:  # pragma: no cover
        _metadata[cls._key_prefix].remove(encoded)
        return False  # untrimmed key

      else:
        # update meta
        _metadata[cls._key_prefix].remove(encoded)
        _metadata['ops']['delete'] = _metadata['ops'].get('delete', 0) + 1
        _metadata['global']['entity_count'] = _metadata['global'].get('entity_count', 1) - 1
        _metadata['kinds'][kind]['entity_count'] = _metadata['kinds'][kind].get('entity_count', 1) - 1

      return True
    return False

  @classmethod
  def allocate_ids(cls, key_class, kind, count=1, **kwargs):

    ''' Allocate new Key IDs up to `count`. '''

    global _metadata

    # resolve kind meta and increment pointer
    kind_blob = _metadata['kinds'].get(kind, {})
    current = kind_blob.get('id_pointer', 0)
    pointer = kind_blob['id_pointer'] = (current + count)

    # update kind blob
    _metadata['kinds'][kind] = kind_blob

    # return IDs
    if count > 1:
      def _generate_id_range():
        for x in xrange(current, pointer):
          yield x
        raise StopIteration()
      return _generate_id_range
    return pointer

  @classmethod
  def write_indexes(cls, writes, **kwargs):

    ''' Write a set of generated indexes via `generate_indexes`. '''

    global _metadata

    # extract indexes
    encoded, meta, properties = writes

    # write indexes one-by-one, generating reverse entries as we go
    for write in meta + [value for serializer, value in properties]:

      # filter out strings, convert to 1-tuples
      if isinstance(write, basestring):  # pragma: no cover
        write = (write,)

      if len(write) > 3:  # hashed/mapped index

        # extract write, inflate
        index, path, value = write[0], write[1:-1], write[-1]

        if isinstance(value, dict):
          continue  # cannot index dictionaries

        # init index hash (mostly covers custom indexes)
        if index not in _metadata:  # pragma: no cover
          _metadata[index] = {(path, value): set()}

        elif (path, value) not in _metadata[index]:
          _metadata[index][(path, value)] = set()

        # write key to index
        _metadata[index][(path, value)].add(encoded)

        # add reverse index
        if encoded not in _metadata[cls._reverse_prefix]:  # pragma: no cover
          _metadata[cls._reverse_prefix][encoded] = set()
        _metadata[cls._reverse_prefix][encoded].add((index, path, value))

        continue

      elif len(write) == 3:  # pragma: no cover
        # @TODO(sgammon): Do we need this?

        # simple map index

        # extract write, inflate
        index, dimension, value = write

        # init index hash
        if index not in _metadata:
          _metadata[index] = {dimension: set((value,))}

        elif dimension not in _metadata[index]:
          _metadata[index][dimension] = set((value,))

        else:
          # everything is there, map the value
          _metadata[index][dimension].add(value)

        # add reverse index
        if encoded not in _metadata[cls._reverse_prefix]:
          _metadata[cls._reverse_prefix][encoded] = set()
        _metadata[cls._reverse_prefix][encoded].add((index, dimension))
        continue

      elif len(write) == 2:  # simple set index

        # extract write, inflate
        index, value = write

        # init index hash
        if index not in _metadata:  # pragma: no cover
          _metadata[index] = {value: set()}

        # init value set
        elif value not in _metadata[index]:
          _metadata[index][value] = set()

        # only provision if value and index are different
        if index != value:

          # add encoded key
          _metadata[index][value].add(encoded)

        # add reverse index
        if encoded not in _metadata[cls._reverse_prefix]:
          _metadata[cls._reverse_prefix][encoded] = set()
        _metadata[cls._reverse_prefix][encoded].add(index)
        continue

      elif len(write) == 1:  # simple key mapping

        # extract singular index
        index = write[0]

        # special case: key index
        if index == cls._key_prefix:
          _metadata[index].add(encoded)
          continue

        # provision index
        if index not in _metadata:  # pragma: no cover
          _metadata[index] = {}

        # add value to index
        _metadata[index][encoded] = set()  # provision with a one-index entry

        # add reverse index
        if encoded not in _metadata[cls._reverse_prefix]:  # pragma: no cover
          _metadata[cls._reverse_prefix][encoded] = set()
        _metadata[cls._reverse_prefix][encoded].add((index,))
        continue

      else:  # pragma: no cover
        raise ValueError("Index mapping tuples must have at least 2 entries,"
                 "for a simple set index, or more for a hashed index.")

  @classmethod
  def clean_indexes(cls, writes, **kwargs):

    ''' Clean indexes for a key. '''

    global _metadata

    # extract indexes
    encoded, meta = writes

    # pull reverse indexes
    reverse = _metadata[cls._reverse_prefix].get(encoded, set())

    # clear reverse indexes
    _cleaned = set()
    if len(reverse) or len(meta):
      for i in reverse | set(meta):

        # convert to tuple to be consistent
        if not isinstance(i, tuple):
          i = (i,)

        # check cleanlist
        if i in _cleaned:  # pragma: no cover
          continue  # we've already cleaned this directive
        else:
          _cleaned.add(i)

        if len(i) == 3:  # hashed index

          # extract write, clean
          index, path, value = i

          if isinstance(path, tuple):
            if index in _metadata and (path, value) in _metadata[index]:
              _metadata[index][(path, value)].remove(encoded)

              # if there's no keys left in the index, trim it
              if len(_metadata[index][(path, value)]) == 0:
                del _metadata[index][(path, value)]

            continue

          # (mostly covers custom indexes)
          if isinstance(path, basestring):  # pragma: no cover
            if index in _metadata and path in _metadata[index]:
              _metadata[index][path].remove(encoded)

              # if there's no keys left in the entry, trim it
              if len(_metadata[index][path]) == 0:
                del _metadata[index][path]

            continue

        elif len(i) == 2:  # simple set index
          # extract write, clean
          index, value = i

          if index in _metadata and value in _metadata[index]:
            _metadata[index][value].remove(encoded)  # remove from set at item in mapping

            # if there's no keys left in the index, trim it
            if len(_metadata[index][value]) == 0:
              del _metadata[index][value]

          continue

        elif len(i) == 1:  # simple key mapping
          if i[0] == '__key__':
            continue  # skip keys, that's done by `delete()`
          if encoded in _metadata[i[0]]:
            del _metadata[i[0]][encoded]

    if encoded in _metadata[cls._reverse_prefix]:
      # last step: remove reverse index for key
      del _metadata[cls._reverse_prefix][encoded]

    return _cleaned

  @classmethod
  def execute_query(cls, kind, spec, options, **kwargs):  # pragma: no cover

    ''' Execute a query across one (or multiple) indexed properties. '''

    raise NotImplementedError('Queries are not yet supported in `InMemoryAdapter`.')


__all__ = ('InMemoryAdapter',)
