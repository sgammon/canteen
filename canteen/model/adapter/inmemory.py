# -*- coding: utf-8 -*-

"""

  in-memory model adapter
  ~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import time
import json
import base64
import datetime
import itertools
import collections

# adapter API
from .abstract import DirectedGraphAdapter


## Globals
_init = False
_graph = {}
_metadata = {}
_datastore = {}


## Constants
_sorted_types = (int,
                 long,
                 float,
                 datetime.date,
                 datetime.datetime)


## Utils
_to_timestamp = lambda dt: int(time.mktime(dt.timetuple()))


class InMemoryAdapter(DirectedGraphAdapter):

  """ Adapt model classes to RAM. """

  # key encoding
  _key_encoder = base64.b64encode

  # data compression / encoding
  _data_encoder = json.dumps
  _data_compressor = None

  is_supported = classmethod(lambda cls: True)  # always supported

  @classmethod
  def acquire(cls, name, bases, properties):

    """ Perform first initialization. """

    global _init, _graph, _metadata

    # perform first init, if it hasn't been done
    if not _init:
      _init, _metadata, _graph = True, {

        'ops': {  # holds count of performed operations
          'get': 0,  # track # of entity get() operations
          'put': 0,  # track # of entity put() operations
          'delete': 0},  # track # of entity delete() operations

        'kinds': {},  # holds current count and ID increment
        'global': {  # holds global metadata, like entity count
          'entity_count': 0,  # holds global count of all entities
          'node_count': 0,  # holds count of known nodes
          'edge_count': 0},  # holds count of known edges

        cls._key_prefix: set([]),  # full, simple indexed set of all keys
        cls._kind_prefix: {},  # maps keys to their kinds
        cls._group_prefix: {},  # maps keys to their entity groups
        cls._index_prefix: {},  # maps property values to keys
        cls._reverse_prefix: {}  # maps keys to indexes they are present in

      }, {
        'nodes': collections.defaultdict(lambda: set()),

        'edges': {
          'directed': {
            'in': collections.defaultdict(lambda: set()),
            'out': collections.defaultdict(lambda: set())},

          'undirected': collections.defaultdict(lambda: set())},

        'neighbors': {
          'directed': {
            'in': collections.defaultdict(lambda: set()),
            'out': collections.defaultdict(lambda: set())},

          'undirected': collections.defaultdict(lambda: set())}
      }

    # pass up the chain to create a singleton
    return super(InMemoryAdapter, cls).acquire(name, bases, properties)

  @classmethod
  def get(cls, key, **kwargs):

    """ Retrieve an entity by Key from Python RAM. """

    global _metadata

    # key format: tuple(<str encoded key>, <tuple flattened key>)
    encoded, flattened = key

    # pull from in-memory backend
    entity = _datastore.get(encoded)
    if entity is None: return  # not found

    _metadata['ops']['get'] += 1

    # construct + inflate entity
    return entity

  @classmethod
  def put(cls, key, entity, model, **kwargs):

    """ Persist an entity to storage in Python RAM. """

    global _graph, _metadata, _datastore

    # encode key and flatten
    encoded, flattened = key

    # perform validation
    with entity:

      if entity.key.kind not in _metadata['kinds']:  # pragma: no cover
        _metadata['kinds'][entity.key.kind] = {
          'id_pointer': 0,  # keep current key ID pointer
          'entity_count': 0}  # keep count of seen entities for each kind

      # update counts
      _metadata['ops']['put'] = _metadata['ops'].get('put', 0) + 1

      _metadata['global']['entity_count'] = (
        _metadata['global'].get('entity_count', 0) + 1)

      kinded_entity_count = (
        _metadata['kinds'][entity.key.kind].get('entity_count', 0))

      _metadata['kinds'][entity.key.kind]['entity_count'] = (
        kinded_entity_count + 1)

      # save to datastore
      _datastore[encoded] = entity.to_dict()

      # store vertexes separately
      if getattr(model, '__vertex__', False):
        _graph['nodes'][entity.key.kind].add(key)

      # store edges separately
      elif getattr(model, '__edge__', False):

        # directed edges
        if model.__spec__.directed:

          left = _graph['neighbors']['directed']['out'][entity['source']]
          left_e = _graph['edges']['directed']['out'][entity['source']]

          for _edge_target in entity['target']:
            right = _graph['neighbors']['directed']['in'][_edge_target]
            right_e = _graph['edges']['directed']['in'][_edge_target]

            # index neighbors to each other
            right.add(entity['source'])
            right_e.add(entity.key)

            # index edges
            left.add(_edge_target)
            left_e.add(entity.key)

        # undirected edges
        else:
          for origin in entity['peers']:
            for target in entity['peers']:
              if origin == target: continue
              _graph['neighbors']['undirected'][origin].add(target)
              _graph['edges']['undirected'][origin].add(entity.key)
              _graph['edges']['undirected'][target].add(entity.key)

    return entity.key

  @classmethod
  def delete(cls, key, **kwargs):

    """ Delete an entity by Key from memory. """

    global _metadata, _datastore

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
        _metadata['ops']['delete'] = (
          _metadata['ops'].get('delete', 0) + 1)

        _metadata['global']['entity_count'] = (
          _metadata['global'].get('entity_count', 1) - 1)

        _metadata['kinds'][kind]['entity_count'] = (
          _metadata['kinds'][kind].get('entity_count', 1) - 1)

      return True
    return False

  @classmethod
  def allocate_ids(cls, key_class, kind, count=1, **kwargs):

    """ Allocate new Key IDs up to `count`. """

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
  def write_indexes(cls, writes, execute=True, **kwargs):

    """ Write a set of generated indexes via `generate_indexes`. """

    global _metadata
    _write = {} if not execute else _metadata

    # extract indexes
    encoded, meta, properties = writes

    # write indexes one-by-one, generating reverse entries as we go
    for serializer, write in itertools.chain(
      ((None, _m) for _m in meta), (bundle for bundle in properties)):

      # filter out strings, convert to 1-tuples
      if isinstance(write, basestring):  # pragma: no cover
        write = (write,)

      if len(write) > 3:  # hashed/mapped index

        # extract write, inflate
        index, path, value = write[0], write[1:-1], write[-1]

        if isinstance(value, dict):  # pragma: no cover
          continue  # cannot index dictionaries

        # convert into a compound sorted index
        if isinstance(value, _sorted_types):

          if isinstance(value, datetime.datetime):
            value = _to_timestamp(value)

          write = (index, path, (value, encoded))

        else:
          # init index hash (mostly covers custom indexes)
          if index not in _write:  # pragma: no cover
            _write[index] = {(path, value): set()}

          elif (path, value) not in _write[index]:
            _write[index][(path, value)] = set()

          # write key to index
          _write[index][(path, value)].add(encoded)

          # add reverse index
          if encoded not in _write[cls._reverse_prefix]:  # pragma: no cover
            _write[cls._reverse_prefix][encoded] = set()
          _write[cls._reverse_prefix][encoded].add((index, path, value))

          continue

      if len(write) == 3:  # pragma: no cover
        # @TODO(sgammon): Do we need this?

        # simple map index

        # extract write, inflate
        index, dimension, value = write

        # init index hash
        if index not in _write:
          _write[index] = {dimension: {value}}

        elif dimension not in _write[index]:
          _write[index][dimension] = {value}

        else:
          # everything is there, map the value
          _write[index][dimension].add(value)

        # add sorted mark, if necessary
        if isinstance(value, tuple) and isinstance(value[0], _sorted_types):
          _mark = (dimension, '__sorted__')
          if _mark not in _write[index]:
            _write[index][_mark] = {}
          _write[index][_mark][encoded] = value

        # add reverse index
        if encoded not in _write[cls._reverse_prefix]:
          _write[cls._reverse_prefix][encoded] = set()
        _write[cls._reverse_prefix][encoded].add((index, dimension))
        continue

      elif len(write) == 2:  # simple set index

        # extract write, inflate
        index, value = write

        # init index hash
        if index not in _write:  # pragma: no cover
          _write[index] = {value: set()}

        # init value set
        elif value not in _write[index]:
          _write[index][value] = set()

        # only provision if value and index are different
        if index != value:

          # add encoded key
          _write[index][value].add(encoded)

        # add reverse index
        if encoded not in _write[cls._reverse_prefix]:
          _write[cls._reverse_prefix][encoded] = set()
        _write[cls._reverse_prefix][encoded].add(index)
        continue

      elif len(write) == 1:  # simple key mapping

        # extract singular index
        index = write[0]

        # special case: key index
        if index == cls._key_prefix:
          _write[index].add(encoded)
          continue

        # provision index
        if index not in _write:  # pragma: no cover
          _write[index] = {}

        # add value to index
        _write[index][encoded] = set()  # provision with a one-index entry

        # add reverse index
        if encoded not in _write[cls._reverse_prefix]:  # pragma: no cover
          _write[cls._reverse_prefix][encoded] = set()
        _write[cls._reverse_prefix][encoded].add((index,))
        continue

      else:  # pragma: no cover
        raise ValueError("Index mapping tuples must have at least 2 entries,"
                         " for a simple set index, or more for a hashed index.")

    return _write

  @classmethod
  def clean_indexes(cls, writes, **kwargs):

    """ Clean indexes for a key. """

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

            # check sorted-ness
            svalue = (value, '__sorted__')
            if svalue in _metadata[index]:
              sorted_entry = _metadata[index][svalue].get(encoded)
              if sorted_entry:
                _metadata[index][value].remove(sorted_entry)

            else:
              # remove from set at item in mapping
              _metadata[index][value].remove(encoded)

            # if there's no keys left in the index, trim it
            if len(_metadata[index][value]) == 0:  # pragma: no cover
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

    """ Execute a query across one (or multiple) indexed properties. """

    from canteen import model
    from canteen.model import query

    # extract spec
    filters, sorts = spec

    # calculate ancestry parent
    ancestry_parent = None
    if isinstance(options.ancestor, basestring):
      ancestry_parent = model.Key.from_urlsafe(options.ancestor)
    elif isinstance(options.ancestor, model.Key):
      ancestry_parent = options.ancestor
    elif isinstance(options.ancestor, model.Model):
      ancestry_parent = options.ancestor.key

    # prepare workspace
    _data_frame, _q_init = set(), False
    _special_indexes, _sorted_indexes, _unsorted_indexes, _inmemory_filters = (
        [], [], [], [])

    _index_groups = (_special_indexes, _sorted_indexes, _unsorted_indexes)

    ## apply ancestry first
    if ancestry_parent:
      _ekey = ancestry_parent.urlsafe()
      _group_index = _metadata[cls._group_prefix].get(_ekey)
      if _group_index: _special_indexes.append((False, (
          query.KeyFilter(_ekey, type=query.KeyFilter.ANCESTOR), _group_index)))

    ## apply filters
    if filters or ancestry_parent:

      for _f in filters:

        if isinstance(_f.value, model.Model._PropertyValue):
          _filter_val = _f.value.data
        else:
          _filter_val = _f.value

        if isinstance(_f.value.data, _sorted_types):

          # convert timestamps
          if isinstance(_f.value.data, (datetime.datetime, datetime.date)):
            _filter_val = _to_timestamp(_f.value.data)

          # valued index
          _index_key = (kind.__name__, _f.target.name)
          if _index_key in _metadata[cls._index_prefix]:
            _sorted_indexes.append((True, (
              _f.target.name,
              _f.operator,
              _filter_val,
              _metadata[cls._index_prefix][_index_key])))

        else:

          if isinstance(_f, query.EdgeFilter):

            _graph_base = 'edges' if _f.kind is _f.EDGES else 'neighbors'

            if _f.tails is None:  # undirected query
              _target_edge_index = (
                _graph[_graph_base]['undirected'].get(_filter_val, set()))

            else:  # directed queries

              _direction = 'out' if _f.tails else 'in'
              _target_edge_index = (
                _graph[_graph_base]['directed'][_direction].get(*(
                    _filter_val, set())))

              #import pdb; pdb.set_trace()

            _unsorted_indexes.append((False, (_f, _target_edge_index)))

          else:
            # devalued index
            _index_key = ((kind.__name__, _f.target.name), _f.value.data)
            if _index_key in _metadata[cls._index_prefix]:
              _unsorted_indexes.append((False, (_f,
                                       _metadata[cls._index_prefix][_index_key])))

      for group in _index_groups:
        for is_sorted, directive in group:

          # sorted indexes
          if is_sorted:
            target, operator, value, index = directive
            high_bound = (value if (operator in (
              query.LESS_THAN, query.LESS_THAN_EQUAL_TO)) else None)
            low_bound = (value if (operator in (
              query.GREATER_THAN, query.GREATER_THAN_EQUAL_TO)) else None)

            if low_bound and not high_bound:
              evaluate = lambda bundle: (low_bound < bundle[0])

            elif low_bound and high_bound:
              evaluate = lambda bundle: (low_bound < bundle[0] < high_bound)

            elif high_bound:  # high-bound only
              evaluate = lambda bundle: (bundle[0] < high_bound)

            else:  # invalid filter
              raise RuntimeError('Invalid sorted filter'
                                 ' operation: "%s".' % operator)

            if not _q_init:  # no frame yet, initialize
              _q_init = True
              _data_frame = (
                set((value for _, value in filter(evaluate, index))))
            else:  # otherwise, filter
              _data_frame &= (
                set((value for _, value in filter(evaluate, index))))

          # unsorted indexes
          else:
            _fblock, _target = directive

            if _fblock.operator in frozenset((query.EQUALS,
                                              query.CONTAINS,
                                              query.KEY_KIND,
                                              query.KEY_ANCESTOR)):

              if not _q_init:  # no frame yet, initialize
                _q_init = True
                _data_frame = _target
              else:
                # filter against selected target
                _data_frame &= _target
            elif _fblock.operator is query.NOT_EQUALS:
              # inequality filters are deferred
              _inmemory_filters.append(_fblock)
            else:  # pragma: no cover
              raise RuntimeError('Invalid query operator "%s" encountered'
                                  ' during execution.' % _fblock.operator)

    elif not filters and not ancestry_parent:
      # no filters - working with _all_ models of a kind as base
      _data_frame = _metadata[cls._kind_prefix].get(kind.__name__)

    ## inflate results (keys only)
    if options.keys_only and not _inmemory_filters:
      _keyify = lambda k: (
        model.Key.from_urlsafe(k, _persisted=True) if not (
          isinstance(k, model.Key)) else k)

      return (_keyify(k) for k in _data_frame)

    result_entities = []

    ## inflate results (full models)
    _seen = 0
    _flatten = lambda _k: _k.urlsafe() if isinstance(_k, model.Key) else _k

    for key, entity in ((k, _datastore[_flatten(k)]) for k in _data_frame):

      if not isinstance(key, model.Key):
        key = model.Key.from_urlsafe(key, _persisted=True)

      if not entity: continue
      if options.limit and _seen >= options.limit:
        break

      # attach key, decode entity and construct
      entity['key'] = key

      # resolve kind class for key and inflate
      if key.kind not in cls.registry and kind.kind() != key.kind:
        raise RuntimeError('Unknown or unregistered key kind: "%s".' % key.kind)
      elif key.kind == kind.kind():
        obj = kind(_persisted=True, **entity)
      else:
        obj = cls.registry.get(key.kind, kind)(_persisted=True, **entity)

      # collapse in-memory filters
      for _inner_f in _inmemory_filters:
        if not _inner_f(obj):
          break
      else:
        _seen += 1
        result_entities.append(obj)

    if not len(result_entities) > 1:
      return result_entities  # no need to sort, obvs

    ## apply sorts
    if sorts:

      def do_sort(sort, results):

        """  """

        _sort_i = set()
        _sort_frame = []
        _sort_values = {}

        # build value index and map to keys
        for result in results:
          val = getattr(result, sort.target.name, None)
          if val is not None:

            if val not in _sort_values:
              _sort_i.add(val)  # add to known values
              _sort_values[val] = set()  # provision value -> obj map
            _sort_values[val].add(result)  # add to map

        _rvs = lambda d: reversed(sorted(d))
        _fwd = lambda d: sorted(d)

        if sort.target._basetype in (basestring, str, unicode):
          sorter = (_rvs if (
                    sort.operator is query.ASCENDING) else _fwd)

        else:
          sorter = (_fwd if (
                    sort.operator is query.ASCENDING) else _rvs)

        # choose iterator and start sorting
        for value in sorter(_sort_i):

          # quick optimization: no need to subgroup, just one sort
          if len(sorts) == 1:
            for _valued_result in _sort_values[value]:
              _sort_frame.append(_valued_result)

          # aww, we have to subgroup and subsort
          if len(sorts) > 1:
            # add sorted groups of values
            _sort_frame.append((value, _sort_values[value]))

        return _sort_frame

      if len(sorts) == 1:
        return do_sort(sorts[0], result_entities)

      if len(sorts) > 1:

        # sort atop the result of the last sort
        _sort_base = []
        for sort in sorts:
          _sort_base = do_sort(*(
            sort, (_sort_base and result_entities) or _sort_base))
        return _sort_base

    return result_entities
