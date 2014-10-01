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
_init, _graph, _metadata, _datastore = (
  False, {}, {}, {})


## Constants
_sorted_types = (int,
                 long,
                 float,
                 datetime.date,
                 datetime.datetime)


## Utils
_to_timestamp = lambda dt: int(time.mktime(dt.timetuple()))


class InMemoryAdapter(DirectedGraphAdapter):

  """ Adapt model classes to RAM with a simple adapter. Mainly meant as a
      reference ``DirectedGraphAdapter`` implementation. Supports querying
      and graph storage. """

  # key encoding
  _key_encoder = base64.b64encode

  # data compression / encoding
  _data_encoder = json.dumps
  _data_compressor = None

  is_supported = classmethod(lambda cls: True)  # always supported

  @classmethod
  def acquire(cls, name, bases, properties):

    """ Perform first initialization.

        :param name: Target :py:class:`Model` subtype class name.
        :param bases: Base classes for target subtype.
        :param properties: Class-level property mappings for target subtype.

        :returns: Prepared :py:class:`InMemoryAdapter` object for target
          ``(name, bases, properties)`` combo. """

    global _init, _graph, _metadata

    # perform first init, if it hasn't been done
    if not _init:
      _init, _metadata, _graph = True, {

        'ops': {  # holds count of performed operations
          'get': 0,  # track # of entity get() operations
          'put': 0,  # track # of entity put() operations
          'delete': 0},  # track # of entity delete() operations

        'keys': set(),  # holds set of all known keys
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

        # holds nodes (structurally)
        'nodes': collections.defaultdict(lambda: set()),

        # holds edges (structurally)
        'edges': {

          # holds directed edges
          'directed': {
            'in': collections.defaultdict(lambda: set()),
            'out': collections.defaultdict(lambda: set())},

          # holds undirected edges
          'undirected': collections.defaultdict(lambda: set())},

        # holds neighbor indexes
        'neighbors': {

          # holds directed edge neighbor indexes
          'directed': {
            'in': collections.defaultdict(lambda: set()),
            'out': collections.defaultdict(lambda: set())},

          # holds undirected neighbor indexes
          'undirected': collections.defaultdict(lambda: set())}}

    # pass up the chain to create a singleton
    return super(InMemoryAdapter, cls).acquire(name, bases, properties)

  @classmethod
  def get(cls, key, **kwargs):

    """ Retrieve an entity by Key from Python RAM.

        :param key: Target :py:class:`model.Key` object at which data should be
          fetched, if it is available.

        :param kwargs: Implementation-specific flags/kwargs passed to the
          underlying adapter from the application.

        :returns: Entity at ``key``, if any, or ``None`` if no entity could
          be found at ``key``. """

    global _metadata

    # key format: tuple(<str encoded key>, <tuple flattened key>)
    encoded, flattened = key

    # pull from in-memory backend
    entity = _datastore.get(flattened)
    if entity is None: return  # not found

    _metadata['ops']['get'] += 1
    return entity  # construct + inflate entity

  @classmethod
  def get_multi(cls, keys, **kwargs):

    """ Retrieve multiple entities in one go by Key from Python RAM.

        :param keys: Iterable of :py:class:`model.Key` objects (or
          ``(encoded, flattened)`` tuple pairs produced from
          ``key.flatten(True)`` to fetch from Python RAM, if they are found to
          be available in underlying storage.

        :param kwargs: Keyword arguments to pass along to the underlying
          driver.

        :returns: Iterable of results for each :py:class:`Key` instance in
          ``keys``, or ``None`` in the place of a result if no matching object
          could be found. """

    from canteen import model

    for key in keys:
      encoded, flattened = key = key if not isinstance(key, model.Key) else (
        key.flatten(True))
      obj = cls.get(key)

      # inflate key + model and return
      obj.key.__persisted__ = True
      yield obj

  @classmethod
  def put(cls, key, entity, model, **kwargs):

    """ Persist an entity to storage in Python RAM.

        :param key: Target :py:class:`model.Key` object at which data should be
          persisted.

        :param entity: Entity object to store against ``key`` in RAM.

        :param model: :py:class:`model.Model` subtype kind for ``entity``. Used
          for property/policy reference.

        :param kwargs: Implementation-specific flags/kwargs to the underlying
          adapter from the application.

        :returns: ``key`` at which ``entity`` was stored in underlying storage,
          including any elements of ``key`` which required population from
           things like ID provisioning. """

    global _graph, _metadata, _datastore

    # encode key and flatten
    encoded, flattened = key
    target = flattened

    # perform validation
    with entity:

      if entity.key.kind not in _metadata['kinds']:  # pragma: no cover
        _metadata['kinds'][entity.key.kind] = {
          'id_pointer': 0,  # keep current key ID pointer
          'entity_count': 0,  # keep count of seen entities for each kind
          'keys': set()}  # keep set of all keys for kind

      # update counts
      _metadata['ops']['put'] = _metadata['ops'].get('put', 0) + 1

      _metadata['global']['entity_count'] = (
        _metadata['global'].get('entity_count', 0) + 1)

      kinded_entity_count = (
        _metadata['kinds'][entity.key.kind].get('entity_count', 0))

      _metadata['kinds'][entity.key.kind]['entity_count'] = (
        kinded_entity_count + 1)

      # add to keys for kind
      kinded_keys = _metadata['kinds'][entity.key.kind].get('keys', set())
      kinded_keys.add(target)
      _metadata['kinds'][entity.key.kind]['keys'] = kinded_keys

      # add to main keys index
      _metadata['keys'].add(target)

      # save to datastore
      _datastore[target] = entity

      # store vertexes separately
      if getattr(model, '__vertex__', False):
        _graph['nodes'][entity.key.kind].add(target)

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

    """ Delete an entity by Key from memory.

        :param key: Target :py:class:`model.Key` object at which data should be
          deleted in underlying RAM storage.

        :param kwargs: Implementation-specific flags/kwargs to the underlying
          adapter from the application.

        :returns: ``True`` if the entity at ``key`` was found and deleted,
          ``False`` if the entity could not be found for deletion. """

    global _metadata, _datastore

    # extract key
    if not isinstance(key, tuple):  # pragma: no cover
      encoded, flattened = key.flatten(True)
    else:
      encoded, flattened = key

    # extract key parts
    parent, kind, _id = flattened

    # if we have the key...
    if flattened in _metadata[cls._key_prefix]:
      try:
        del _datastore[flattened]  # delete from datastore

      except KeyError:  # pragma: no cover
        _metadata[cls._key_prefix].remove(flattened)
        return False  # untrimmed key

      else:
        # update meta
        _metadata[cls._key_prefix].remove(flattened)
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

    """ Allocate new Key IDs up to `count`.

        :param key_class: :py:class:`model.Key` subtype for which we are
          allocating integer IDs from underlying RAM storage.

        :param kind: ``str`` or ``unicode`` kind name for which we are
          allocating integer IDs from underlying RAM storage. Used to resolve
          an appropriate ``id_pointer`` index.

        :param count: Number of unique key IDs we would like to provision.
          Defaults to ``1``.

        :param kwargs: Implementation-specific flags/kwargs to the underlying
          adapter from the application.

        :raises StopIteration: When all the requested IDs have been allocated
          and yielded to the application.

        :returns: If a ``count`` is given that is ``> 1``, will return a
          generator function that will ``yield`` IDs up to ``count`` one at a
          time. Otherwise, returns the newly-provisioned ID integer directly,
          making the return type either ``function`` (if ``count`` is greater
          than one) or ``int``/``long``. """

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
  def write_indexes(cls, writes, _graph, execute=True):

    """ Write a set of generated indexes via `generate_indexes`.

        :param writes: Index writes to commit to the ``_metadata`` ``dict``.

        :param _graph: Graph writes to commit. Ignored in this adapter as those
          are handled in ``put`` instead.

        :param execute: ``bool`` flag, whether to execute and actually commit
          the writes planned.

        :raises RuntimeError: If an invalid bundle of index writes is provided.

        :returns: Writes committed to the ``_metadata`` ``dict``, for
          inspection. """

    global _metadata

    _write = {} if not execute else _metadata

    # extract indexes
    target, meta, properties = writes

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

          write = (index, path, (value, target))

        else:
          # init index hash (mostly covers custom indexes)
          if index not in _write:  # pragma: no cover
            _write[index] = {(path, value): set()}

          elif (path, value) not in _write[index]:
            _write[index][(path, value)] = set()

          # write key to index
          _write[index][(path, value)].add(target)

          # add reverse index
          if target not in _write[cls._reverse_prefix]:  # pragma: no cover
            _write[cls._reverse_prefix][target] = set()
          _write[cls._reverse_prefix][target].add((index, path, value))

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
          _write[index][_mark][target] = value

        # add reverse index
        if target not in _write[cls._reverse_prefix]:
          _write[cls._reverse_prefix][target] = set()
        _write[cls._reverse_prefix][target].add((index, dimension))
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

          # add flattened key
          _write[index][value].add(target)

        # add reverse index
        if target not in _write[cls._reverse_prefix]:
          _write[cls._reverse_prefix][target] = set()
        _write[cls._reverse_prefix][target].add(index)
        continue

      elif len(write) == 1:  # simple key mapping

        # extract singular index
        index = write[0]

        # special case: key index
        if index == cls._key_prefix:
          _write[index].add(target)
          continue

        # provision index
        if index not in _write:  # pragma: no cover
          _write[index] = {}

        # add value to index
        _write[index][target] = set()  # provision with a one-index entry

        # add reverse index
        if target not in _write[cls._reverse_prefix]:  # pragma: no cover
          _write[cls._reverse_prefix][target] = set()
        _write[cls._reverse_prefix][target].add((index,))
        continue

      else:  # pragma: no cover
        raise RuntimeError("Index mapping tuples must have at least 2 entries,"
                           " for a simple set index, or more for"
                           " a hashed index.")

    return _write

  @classmethod
  def clean_indexes(cls, writes, **kwargs):

    """ Clean indexes for a key that is due to be deleted.

        :param writes: Index writes that would be committed if the ``key`` was
          being written. Used to provide a directory of index items to clean
          from underlying RAM.

        :param kwargs: Implementation-specific flags/kwargs to the underlying
          adapter from the application.

        :returns: ``set`` instance containing index keys that were cleaned. """

    global _metadata

    target, meta, graph = writes  # extract indexes

    # pull reverse indexes
    reverse = _metadata[cls._reverse_prefix].get(target, set())

    _cleaned = set()  # clear reverse indexes
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
              _metadata[index][(path, value)].remove(target)

              # if there's no keys left in the index, trim it
              if len(_metadata[index][(path, value)]) == 0:
                del _metadata[index][(path, value)]

            continue

          # (mostly covers custom indexes)
          if isinstance(path, basestring):  # pragma: no cover
            if index in _metadata and path in _metadata[index]:
              _metadata[index][path].remove(target)

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
              sorted_entry = _metadata[index][svalue].get(target)
              if sorted_entry:
                _metadata[index][value].remove(sorted_entry)

            else:
              # remove from set at item in mapping
              _metadata[index][value].remove(target)

            # if there's no keys left in the index, trim it
            if len(_metadata[index][value]) == 0:  # pragma: no cover
              del _metadata[index][value]

          continue

        elif len(i) == 1:  # simple key mapping
          if i[0] == '__key__':
            continue  # skip keys, that's done by `delete()`
          if target in _metadata[i[0]]:
            del _metadata[i[0]][target]

    if target in _metadata[cls._reverse_prefix]:
      # last step: remove reverse index for key
      del _metadata[cls._reverse_prefix][target]

    return _cleaned

  @classmethod
  def encode_key(cls, joined, flattened):

    """ Encode a :py:class:`model.Key` for storage. For ``InMemoryAdapter``,
        simply use the flattened tuple as an internal representation of the
        key.

        :param key: Target :py:class:`model.Key` to encode.

        :param joined: Joined/stringified key.

        :param flattened: Flattened ``tuple`` (raw) key.

        :returns: The encoded :py:class:`model.Key`, or ``False`` to
              yield to the default encoder. """

    return flattened

  @classmethod
  def execute_query(cls, kind, spec, options, **kwargs):  # pragma: no cover

    """ Execute a query across one (or multiple) indexed properties. Collapses
        a symbolic :py:class:`canteen.model.query.Query` object and attempts to
        properly satisfy any ``Filter``/``Sort`` objects attached.

        :param kind: :py:class:`model.Model` subtype class that we're querying
          for. Used for resolving policy/index names/storage names.

        :param spec: Tuple of ``(filters, sorts)`` to apply for this ``Query``
          execution run.

        :param options: :py:class:`canteen.model.query.QueryOptions` instance,
          which specifies query options like a result ``offset`` or ``limit``.

        :param kwargs: Implementation-specific flags/kwargs to the underlying
          adapter from the application.

        :raises RuntimeError: In the event of an unsatisfiable query or other
          unrecoverable runtime error.

        :returns: Results matching ``spec`` for ``kind`` according to
          ``options``, or an empty ``list`` if no results could be found. """

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
      _ekey = cls.encode_key(*ancestry_parent.flatten(True))
      _group_index = _metadata[cls._group_prefix].get(_ekey)
      if _group_index: _special_indexes.append((False, (
          query.KeyFilter(model.Key.from_raw(_ekey),
                          _type=query.KeyFilter.ANCESTOR), _group_index)))

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

            _unsorted_indexes.append((False, (_f, _target_edge_index)))

          else:
            # devalued index
            _index_key = ((kind.__name__, _f.target.name), _f.value.data)
            if _index_key in _metadata[cls._index_prefix]:
              _unsorted_indexes.append((
                False, (_f, _metadata[cls._index_prefix][_index_key])))

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
      _data_frame = _metadata[cls._kind_prefix].get(kind.__name__, set())

    ## inflate results (keys only)
    if options.keys_only and not _inmemory_filters:
      _keyify = lambda k: (
        model.Key.from_urlsafe(k, _persisted=True) if not (
          isinstance(k, model.Key)) else k)

      return (_keyify(k) for k in _data_frame)

    result_entities = []

    if not _data_frame and _inmemory_filters:
      # corner case: no initial data frame but inmemory filters
      #  force-initialize data frame with kind index, or if we're unlucky
      #  enough to be doing a kindless query, the index of all available
      #  keys.

      if kind:
        _data_frame = (
          _metadata['kinds'].get(kind.__name__, {'keys': set()})['keys'])
      else: _data_frame = _metadata['keys']

    for n, (key, entity) in (
          enumerate(((k, _datastore.get(k)) for k in _data_frame))):

      # @TODO(sgammon) log ghosts?
      if not entity: continue  # skip missing entities

      # stop if options say so, skip if the options say so
      if options.limit and n >= options.limit: break
      if options.offset and n <= options.offset: continue
      # @TODO(sgammon): make sure we don't get any off-by-ones

      # collapse in-memory filters
      for _inner_f in _inmemory_filters:
        if not _inner_f(entity):
          break
      else:
        result_entities.append(entity)

    if not result_entities: return result_entities  # no need to sort, obvs

    ## apply sorts
    if sorts:

      def do_sort(_sort, results):

        """ Apply a ``sort`` operation to a set of query ``results``.

            :param sort: :py:class:`canteen.model.query.Sort` instance
              describing the sort operator to be applied and the target
              ``prop`` to apply it to.

            :param results: ``list`` of datastore ``results`` that have been
             filtered and retrieved from underlying storage.

            :returns: Query results passed in as ``results``, but sorted
              according to ``sort``. """

        _sort_i, _sort_frame, _sort_values = set(), [], {}

        # build value index and map to keys
        for result in results:
          val = getattr(result, _sort.target.name, None)
          if val is not None:
            if val not in _sort_values:
              _sort_i.add(val)  # add to known values
              _sort_values[val] = set()  # provision value -> obj map
            _sort_values[val].add(result)  # add to map

        _rvs, _fwd = lambda d: reversed(sorted(d)), lambda d: sorted(d)

        if _sort.target.basetype in (basestring, str, unicode):
          sorter = (_rvs if (_sort.operator is query.ASCENDING) else _fwd)

        else:
          sorter = (_fwd if (_sort.operator is query.ASCENDING) else _rvs)

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
