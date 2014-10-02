# -*- coding: utf-8 -*-

"""

  redis model adapter
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
from operator import itemgetter

# adapter API
from . import abstract
from .abstract import (IndexedModelAdapter,
                       DirectedGraphAdapter)

# canteen util
from canteen.util import struct
from canteen.util import decorators


## Globals
_support = struct.WritableObjectProxy()
_mock_redis = None  # holds global singleton for mock testing
_server_profiles = {}  # holds globally-configured server profiles
_default_profile = None  # holds the default redis instance mapping
_client_connections = {}  # holds instantiated redis connection clients
_profiles_by_model = {}  # holds specific model => redis instance mappings
_SERIES_BASETYPES = (  # basetypes that should be stored as a sorted set
  datetime.datetime, datetime.date, float)


##### ==== runtime ==== #####

# resolve redis
try:
  ## force absolute import to avoid infinite recursion
  redis = _redis_client = _support.redis = (
    __import__('redis', locals(), globals(), [], 0))
except ImportError:  # pragma: no cover
  _support.redis, _redis_client, redis = False, None, None

# or fakeredis, for testing only
try:
  import fakeredis; _support.fakeredis = True
except ImportError:  # pragma: no cover
  fakeredis, _support.fakeredis = None, False

# resolve gevent
try:
  import gevent; _support.gevent = gevent
except ImportError:  # pragma: no cover
  gevent, _support.gevent = None, False
else:  # pragma: no cover
  if _support.redis and (
    hasattr(redis.connection, 'socket') and hasattr(gevent, 'socket')):
    ## with Redis AND gevent, patch the connection socket / pool
    redis.connection.socket = gevent.socket


##### ==== serializers ==== #####

# resolve msgpack
try:
  import msgpack; _support.msgpack = msgpack
except ImportError:  # pragma: no cover
  msgpack, _support.msgpack = None, False


##### ==== compressors ==== #####

# resolve zlib
try:
  import zlib; _support.zlib = zlib
except ImportError:  # pragma: no cover
  zlib, _support.zlib = None, False

# resolve snappy
try:
  import snappy; _support.snappy = snappy
except ImportError:  # pragma: no cover
  snappy, _support.snappy = None, False

# resolve lz4
try:
  import lz4; _support.lz4 = lz4
except ImportError:  # pragma: no cover
  lz4, _support.lz4 = None, False


class RedisMode(object):

  """ Map of hard-coded modes of internal operation for the `RedisAdapter`. """

  hashkey_hash = 'hashkey'  # HSET <key>, <field> => <value> [...]
  hashkey_blob = 'hashblob'  # HSET <entity_group>, <key_id>, <entity>
  hashkind_blob = 'hashkind'  # HSET <kind>, <key_id>, <entity>
  toplevel_blob = 'toplevel'  # SET <key>, <entity>


class RedisAdapter(DirectedGraphAdapter):

  """ Adapt model classes to Redis. """

  __testing__ = False  # are we testing redis?

  # key encoding
  adapter = _redis_client
  connection_spec = None

  # magic string identifiers
  _id_prefix = '__id__'
  _meta_prefix = '__meta__'
  _kind_prefix = '__kind__'
  _magic_separator = '::'
  _path_separator = '.'
  _chunk_separator = ':'


  class EngineConfig(object):

    """ Configuration for the `RedisAdapter` engine. """

    encoding = True  # encoding for keys and special values
    serializer = json  # json or msgpack
    compression = False  # compression for serialized data values
    mode = RedisMode.toplevel_blob  # internal mode of operation


  class Operations(object):

    """ Available datastore operations. """

    ## Key Operations
    SET = 'SET'
    GET = 'GET'
    KEYS = 'KEYS'
    DUMP = 'DUMP'
    DELETE = 'DEL'
    EXISTS = 'EXISTS'
    EXPIRE = 'EXPIRE'
    EXPIRE_AT = 'EXPIREAT'
    MIGRATE = 'MIGRATE'
    MOVE = 'MOVE'
    GETBIT = 'GETBIT'
    GETSET = 'GETSET'
    GETRANGE = 'GETRANGE'
    OBJECT = 'OBJECT'
    PERSIST = 'PERSIST'
    PEXPIRE = 'PEXPIRE'
    PEXPIREAT = 'PEXPIREAT'
    PTTL = 'TTL'
    RANDOM = 'RANDOMKEY'
    RENAME = 'RENAME'
    RENAMENX = 'RENAMENX'
    RESTORE = 'RESTORE'
    SORT = 'SORT'
    TTL = 'TTL'
    TYPE = 'TYPE'
    SCAN = 'SCAN'

    ## Multi-Operations
    MULTI_GET = 'MGET'
    MULTI_SET = 'MSET'

    ## Counter Operations
    INCREMENT = 'INCR'
    DECREMENT = 'DECR'
    INCREMENT_BY = 'INCRBY'
    DECREMENT_BY = 'DECRBY'
    INCREMENT_BY_FLOAT = 'INCRBYFLOAT'

    ## Hash Operations
    HASH_SET = 'HSET'
    HASH_GET = 'HGET'
    HASH_KEYS = 'HKEYS'
    HASH_SCAN = 'HSCAN'
    HASH_DELETE = 'HDEL'
    HASH_LENGTH = 'HLEN'
    HASH_VALUES = 'HVALS'
    HASH_EXISTS = 'HEXISTS'
    HASH_GET_ALL = 'HGETALL'
    HASH_SET_SAFE = 'HSETNX'
    HASH_MULTI_GET = 'HMGET'
    HASH_MULTI_SET = 'HMSET'
    HASH_INCREMENT = 'HINCRBY'
    HASH_INCREMENT_FLOAT = 'HINCRBYFLOAT'

    ## String Commands
    APPEND = 'APPEND'
    STRING_LENGTH = 'STRLEN'

    ## List Operations
    LIST_SET = 'LSET'
    LEFT_POP = 'LPOP'
    RIGHT_POP = 'RPOP'
    LEFT_PUSH = 'LPUSH'
    RIGHT_PUSH = 'RPUSH'
    LEFT_PUSH_X = 'LPUSHX'
    RIGHT_PUSH_X = 'RPUSHX'
    LIST_TRIM = 'LTRIM'
    LIST_INDEX = 'LINDEX'
    LIST_RANGE = 'LRANGE'
    LIST_LENGTH = 'LLEN'
    LIST_REMOVE = 'LREM'
    BLOCK_LEFT_POP = 'BLPOP'
    BLOCK_RIGHT_POP = 'BRPOP'

    ## Set Operations
    SET_ADD = 'SADD'
    SET_POP = 'SPOP'
    SET_MOVE = 'SMOVE'
    SET_DIFF = 'SDIFF'
    SET_UNION = 'SUNION'
    SET_REMOVE = 'SREM'
    SET_MEMBERS = 'SMEMBERS'
    SET_INTERSECT = 'SINTER'
    SET_IS_MEMBER = 'SISMEMBER'
    SET_DIFF_STORE = 'SDIFFSTORE'
    SET_CARDINALITY = 'SCARD'
    SET_UNION_STORE = 'SUNIONSTORE'
    SET_RANDOM_MEMBER = 'SRANDMEMBER'
    SET_INTERSECT_STORE = 'SINTERSTORE'

    ## Sorted Set Operations
    SORTED_ADD = 'ZADD'
    SORTED_RANK = 'ZRANK'
    SORTED_RANGE = 'ZRANGE'
    SORTED_SCORE = 'ZSCORE'
    SORTED_COUNT = 'ZCOUNT'
    SORTED_REMOVE = 'ZREM'
    SORTED_CARDINALITY = 'ZCARD'
    SORTED_UNION_STORE = 'ZUNIONSTORE'
    SORTED_INCREMENT_BY = 'ZINCRBY'
    SORTED_INDEX_BY_SCORE = 'ZREVRANK'
    SORTED_RANGE_BY_SCORE = 'ZRANGEBYSCORE'
    SORTED_INTERSECT_STORE = 'ZINTERSTORE'
    SORTED_MEMBERS_BY_INDEX = 'ZREVRANGE'
    SORTED_MEMBERS_BY_SCORE = 'ZREVRANGEBYSCORE'
    SORTED_REMOVE_RANGE_BY_RANK = 'ZREMRANGEBYRANK'
    SORTED_REMOVE_RANGE_BY_SCORE = 'ZREMRANGEBYSCORE'

    ## Pub/Sub Operations
    PUBLISH = 'PUBLISH'
    SUBSCRIBE = 'SUBSCRIBE'
    UNSUBSCRIBE = 'UNSUBSCRIBE'
    PATTERN_SUBSCRIBE = 'PSUBSCRIBE'
    PATTERN_UNSUBSCRIBE = 'PUNSUBSCRIBE'

    ## Transactional Operations
    EXEC = 'EXEC'
    MULTI = 'MULTI'
    WATCH = 'WATCH'
    UNWATCH = 'UNWATCH'
    DISCARD = 'DISCARD'

    ## Scripting Operations
    EVALUATE = 'EVAL'
    EVALUATE_STORED = 'EVALSHA'
    SCRIPT_LOAD = ('SCRIPT', 'LOAD')
    SCRIPT_KILL = ('SCRIPT', 'KILL')
    SCRIPT_FLUSH = ('SCRIPT', 'FLUSH')
    SCRIPT_EXISTS = ('SCRIPT', 'EXISTS')

    ## Connection Operations
    ECHO = 'ECHO'
    PING = 'PING'
    QUIT = 'QUIT'
    SELECT = 'SELECT'
    AUTHENTICATE = 'AUTH'

    ## Server Operations
    TIME = 'TIME'
    SYNC = 'SYNC'
    SAVE = 'SAVE'
    INFO = 'INFO'
    DEBUG = ('DEBUG', 'OBJECT')
    DB_SIZE = 'DBSIZE'
    SLOWLOG = 'SLOWLOG'
    MONITOR = 'MONITOR'
    SLAVE_OF = 'SLAVEOF'
    SHUTDOWN = 'SHUTDOWN'
    FLUSH_DB = 'FLUSHDB'
    FLUSH_ALL = 'FLUSHALL'
    LAST_SAVE = 'LASTSAVE'
    CONFIG_GET = ('CONFIG', 'GET')
    CONFIG_SET = ('CONFIG', 'SET')
    CLIENT_KILL = ('CLIENT', 'KILL')
    CLIENT_LIST = ('CLIENT', 'LIST')
    CLIENT_GET_NAME = ('CLIENT', 'GETNAME')
    CLIENT_SET_NAME = ('CLIENT', 'SETNAME')
    CONFIG_RESET_STAT = ('CONFIG', 'RESETSTAT')
    BACKGROUND_SAVE = 'BGSAVE'
    BACKGROUND_REWRITE = 'BGREWRITEAOF'

  @classmethod
  def __repr__(cls):  # pragma: no cover

    """ Generate a pleasant string representation of the currently-active
        ``RedisAdapter``.

        :returns: Pretty string with config info. """

    return "%s(mode=%s, serializer=%s, compression=%s)" % (
              cls.__name__,
              cls.EngineConfig.mode,
              cls.EngineConfig.serializer and (
                cls.EngineConfig.serializer.__name__),
              cls.EngineConfig.compression and (
                cls.EngineConfig.compression.__name__))

  __unicode__ = __str__ = __repr__

  @classmethod
  def is_supported(cls):

    """ Check whether this adapter is supported in the current environment.

        :returns: The imported ``Redis`` driver, or ``False`` if it could not
          be found. """

    if cls.__testing__ and fakeredis:  # pragma: no cover
      return _support.fakeredis
    return _support.redis

  @decorators.classproperty
  def serializer(cls):  # pragma: no cover

    """ Load and return the optimal serialization codec.

        :returns: Currently-configured serializer, mounted statically at
          ``cls.EngineConfig.serializer``. """

    return msgpack if _support.msgpack else json

  @decorators.classproperty
  def compressor(cls):  # pragma: no cover

    """ Load and return the optimal data compressor.

        :returns: Currently-configured compressor, mounted statically at
          ``cls.EngineConfig.compression``. """

    return cls.EngineConfig.compression or zlib

  @classmethod
  def acquire(cls, name, bases, properties):

    """  """

    return super(RedisAdapter, cls).acquire(name, bases, properties)

  def __init__(self):

    """  """

    global _server_profiles
    global _default_profile
    global _profiles_by_model

    ## Resolve default
    servers = self.config.get('servers', False)

    if not _default_profile:

      ## Resolve Redis config
      if servers:  # pragma: no cover
        for name, config in servers.items():
          if name == 'default' or (config.get('default', False) is True):
            _default_profile = name
          elif not _default_profile:  # pragma: no cover
            _default_profile = name
          if isinstance(config, basestring):
            _server_profiles[name] = redis.from_url(config)
          else:
            _server_profiles[name] = config

      if not _default_profile:
        # still no default? inject sensible defaults
        _default_profile = '__default__'
        _server_profiles['__default__'] = {
          'host': '127.0.0.1', 'port': 6379}

  @classmethod
  def channel(cls, kind):

    """ Retrieve a write channel to Redis.

        :param kind: String :py:class:`model.Model` kind to retrieve a channel
          for.

        :raises RuntimeError:

        :returns: Acquired ``Redis`` client connection, potentially specific to
          the handed-in ``kind``. """

    global _mock_redis

    if not cls.adapter or not _support.redis:  # pragma: no cover
      raise RuntimeError('No support detected in the current environment'
                         ' for Python Redis. Please `pip install redis`.')

    if not (__debug__ and cls.__testing__):  # pragma: no cover

      impl, pool, profile = (
        cls.adapter.StrictRedis, cls.adapter.ConnectionPool, None)

      # convert to string kind if we got a model class
      if not isinstance(kind, basestring) and kind is not None:
        kind = kind.kind()

      # check for existing connection
      if kind in _client_connections:
        return _client_connections[kind]  # return cached connection

      # check kind-specific profiles
      if kind in _profiles_by_model.get('index', set()):  # pragma: no cover
        profile = _profiles_by_model['map'].get(kind)
        if 'unix_socket_path' in profile:
          client = _client_connections[kind] = (
            impl(**profile))
          return client

        max_connections = profile.get('max_connections', 1000)
        if 'max_connections' in profile:
          del profile['max_connections']
        client = _client_connections[kind] = pool(
          max_connections=max_connections, **profile)
        return impl(connection_pool=client)

      # # @TODO(sgammon): patch client with connection/workerpool (if gevent)

      # check for cached default connection
      if '__default__' in _client_connections:
        return _client_connections['__default__']

      _config = cls.config
      if 'servers' in _config:
        profile = _config['servers'].get('default', None)
        profile = _config['servers'].get(profile, None)
        if profile: return impl(**profile)

      # otherwise, build new default
      default_profile = profile = _server_profiles[_default_profile]
      if isinstance(default_profile, basestring):
        # if it's a string, it's a pointer to a profile
        profile = _server_profiles[default_profile]

      client = _client_connections['__default__'] = impl(**profile)
      return client

    else:  # pragma: no cover

      # mock adapter testing
      import fakeredis

      if not _mock_redis:
        _mock_redis = fakeredis.FakeStrictRedis()
      return _mock_redis

  @classmethod
  def execute(cls, operation, kind, *args, **kwargs):

    """ Acquire a channel and execute an operation, optionally buffering the
        command.

        :param operation: Operation name to execute (from
          :py:attr:`RedisAdapter.Operations`).

        :param kind: String :py:class:`model.Model` kind to acquire the channel
          for.

        :param args: Positional arguments to pass to the low-level operation
          selected.

        :param kwargs: Keyword arguments to pass to the low-level operation
          selected.

        :returns: Result of the selected low-level operation. """

    # defer to pipeline or resolve channel for kind
    target = kwargs.get('target', None)
    if target is None: target = cls.channel(kind)

    if operation == cls.Operations.DELETE:
      # special case: `delete` instead of `del` (because it's a keyword)
      operation = 'DELETE'

    if 'target' in kwargs: del kwargs['target']

    try:
      if isinstance(operation, tuple):  # pragma: no cover
        # (CLIENT, KILL) => "CLIENT KILL"
        operation = '_'.join(map(unicode, operation))
      if isinstance(target, (_redis_client.client.Pipeline,
                             _redis_client.client.StrictPipeline)) or (
              fakeredis and isinstance(target, fakeredis.FakePipeline)):
        getattr(target, operation.lower())(*args, **kwargs)
        return target
      if operation == cls.Operations.HASH_SET:  # pragma: no cover
        r = getattr(target, operation.lower())(*args, **kwargs)
        if r in (0, 1):
          # count 0 and 1 as success, as it indicates an overwrite,
          # not a failure
          return 1
      return getattr(target, operation.lower())(*args, **kwargs)
    except Exception:  # pragma: no cover
      raise

  @classmethod
  def inflate(cls, result):

    """ Small closure that can inflate (and potentially decompress) a resulting
        object for a given storage mode.

        :param result: ``basestring`` result from raw Redis storage.

        :returns: Inflated entity, if applicable. """

    if not isinstance(result, basestring):  # pragma: no cover
      return result  # accounts for dict-like storage

    # account for none, optionally decompress
    if cls.EngineConfig.compression:  # pragma: no cover
      try:
        result = cls.compressor.decompress(result)
      except:
        pass  # maybe entity is uncompressed? will fail during deserialization

    # deserialize structures
    return cls.serializer.loads(result)

  @classmethod
  def get(cls, key, pipeline=None, _entity=None):

    """ Retrieve an entity by Key from Redis.

        :param key: Target :py:class:`model.Key` to retrieve from storage.

        :param pipeline: Redis pipeline to enqueue the resulting commands
          in, rather than directly executing them. Defaults to ``None``. If a
          pipeline is passed, it will be returned in lieu of the pending
          result.

        :param _entity: Entity to inflate, if we already have one.

        :returns: The deserialized and decompressed entity associated with the
          target ``key``. """

    from canteen import model

    if key:
      encoded, flattened = key

      # @TODO(sgammon): access to structured keys in adapters
      joined, _ = model.Key.from_urlsafe(encoded).flatten(True)

      ## toplevel_blob
      if cls.EngineConfig.mode == RedisMode.toplevel_blob:

        # execute query
        result = _entity or (
          cls.execute(cls.Operations.GET, flattened[1],
                        encoded,
                        target=pipeline))

      ## hashkind_blob
      elif cls.EngineConfig.mode == RedisMode.hashkind_blob:

        # generate kinded key and trim tail
        j_kinded, f_kinded = model.Key(flattened[1]).flatten(True)
        tail = joined.replace(j_kinded, '')

        result = _entity or (
          cls.execute(*(
            cls.Operations.HASH_GET,
            flattened[1],
            cls.encode_key(j_kinded, f_kinded),
            cls.encode_key(tail, flattened)), target=pipeline))

      ## hashkey_blob
      elif cls.EngineConfig.mode == RedisMode.hashkey_blob:

        # build key and extract group
        desired_key = model.Key.from_raw(joined)
        root = (ancestor for ancestor in desired_key.ancestry).next()
        tail = (
          desired_key.flatten(True)[0].replace(root.flatten(True)[0], '') or (
            '__root__'))

        result = _entity or (
          cls.execute(*(
            cls.Operations.HASH_GET,
            flattened[1],
            cls.encode_key(*root.flatten(True)),
            cls.encode_key(tail, flattened)), target=pipeline))

      ## hashkey_hash
      elif cls.EngineConfig.mode == RedisMode.hashkey_hash:  # pragma: no cover

        raise NotImplementedError('Redis mode not implemented: "hashkey_hash".')

      else:  # pragma: no cover
        raise NotImplementedError("Unknown storage mode: '%s'." % (
                                                        cls.EngineConfig.mode))

    else:  # pragma: no cover
      result = _entity

    # @TODO: different storage internal modes
    if isinstance(result, basestring):
      return cls.inflate(result)
    return result

  @classmethod
  def get_multi(cls, keys, pipeline=None, **kwargs):

    """ Retrieve a set of entity by Key from Redis, all in one go.

        :param keys: Target iterable of :py:class:`model.Key` instances to
          retrieve from storage.

        :param pipeline: Pipeline to execute commands against, if any.

        :param kwargs: Implementation-specific kwargs passed through from the
          original caller.

        :returns: The deserialized and decompressed entity associated with the
          target ``key``. """

    from canteen import model

    if keys:
      requested_keys = keys
      results, calls, bundles, handler = {}, [], [], {
          RedisMode.toplevel_blob: cls.Operations.MULTI_GET,
          RedisMode.hashkind_blob: cls.Operations.HASH_MULTI_GET,
          RedisMode.hashkey_blob: cls.Operations.HASH_MULTI_GET,
          RedisMode.hashkey_hash: cls.Operations.HASH_GET_ALL
        }.get(cls.EngineConfig.mode)

      # # plan reads
      for _k in keys:
        encoded, flattened = _k

        if cls.EngineConfig.mode == RedisMode.toplevel_blob:
          bundles.append((flattened[1], encoded, _k))

        elif cls.EngineConfig.mode == RedisMode.hashkind_blob:
          # @TODO(sgammon): access to structured keys in adapters
          joined, _ = model.Key.from_urlsafe(encoded).flatten(True)

          # generate kinded key and trim tail
          j_kinded, f_kinded = model.Key(flattened[1]).flatten(True)
          tail = joined.replace(j_kinded, '')

          # encode
          encoded_root, encoded_tail = (
            cls.encode_key(j_kinded, f_kinded),
            cls.encode_key(tail, flattened))

          bundles.append((flattened[1], encoded_root, encoded_tail, _k))

        elif cls.EngineConfig.mode == RedisMode.hashkey_blob:
          # @TODO(sgammon): access to structured keys in adapters
          joined, _target = model.Key.from_urlsafe(encoded).flatten(True)

          # build key and extract group
          desired_key = model.Key.from_raw(joined)
          root = (ancestor for ancestor in desired_key.ancestry).next()
          tail = (
            desired_key.flatten(True)[0].replace(root.flatten(True)[0], '') or (
              '__root__'))

          encoded_root, encoded_tail = (
            cls.encode_key(*root.flatten(True)),
            cls.encode_key(tail, flattened))

          bundles.append((flattened[1], encoded_root, encoded_tail, _k))

        elif cls.EngineConfig.mode == RedisMode.hashkey_hash:
          raise NotImplementedError('Redis mode not implemented:'
                                    ' "hashkey_hash.')  # pragma: no cover

      ## merge reads
      kinds, keys, expected, requested = (
        set(), collections.OrderedDict(), [], collections.OrderedDict())

      for read in bundles:
        if cls.EngineConfig.mode == RedisMode.toplevel_blob:
          # merge keys, not kinds (no namespacing by kind so MGET works)
          kind, encoded, _k = read
          kinds.add(kind)

          if kind not in keys:
            keys[kind], requested[kind] = [], []
          keys[kind].append(encoded)
          requested[kind].append(_k)

        elif cls.EngineConfig.mode == RedisMode.hashkind_blob or (
              cls.EngineConfig.mode == RedisMode.hashkey_blob):
          kind, root, tail, _k = read

          if root not in keys:
            keys[root], requested[root] = [], []
          keys[root].append(tail)
          requested[root].append(_k)

      # @TODO(sgammon): reads segmented in toplevel by kind, because of routing?
      pipeline = pipeline or cls.channel('__meta__').pipeline(transaction=False)
      with pipeline as pipe:

        ## collapse reads
        if cls.EngineConfig.mode == RedisMode.toplevel_blob:
          for kind in kinds:

            # track expected keys with calls
            expected.append([i for i in requested[kind]])
            cls.execute(handler, kind, *[i for i in keys[kind]], target=pipe)

        elif cls.EngineConfig.mode == RedisMode.hashkind_blob or (
              cls.EngineConfig.mode == RedisMode.hashkey_blob):
          for root in keys:

            _expected, tails = (
              [r for r in requested[root]], [tail for tail in keys[root]])

            expected.append(_expected)  # combine into a single call

            # if there's only one fetch from this hash, do an HGET instead
            if len(tails) == 1 and cls.EngineConfig.mode in (
                  RedisMode.hashkey_blob,
                  RedisMode.hashkind_blob):
              _target_handler = cls.Operations.HASH_GET
            else:
              _target_handler = handler
            cls.execute(_target_handler, '__meta__', root, *tails, target=pipe)

        resultset = pipe.execute()  # execute pipeline and inflate

        for keygroup, item in zip(expected, resultset):
          if not isinstance(item, (tuple, list)):
            item = (item,)

          for key, entity in zip(keygroup, item):
            results[key] = (
              cls.inflate(entity) if isinstance(entity, basestring) else entity)

        inflated_results = []
        for key in requested_keys:
          entity = results.get(key)

          if not entity:
            inflated_results.append(None)
          else:
            encoded, flattened = key
            entity['key'] = (
              cls.registry[flattened[1]].__keyclass__.from_raw(
                base64.b64decode(encoded)))

            inflated_results.append(
              cls.registry[flattened[1]](_persisted=True, **entity))

      return inflated_results

  def _put(self, entity, **kwargs):  # pragma: no cover

    """ Overrides low-level ``put`` process to enable pipelining of object
        writes with their indexes.

        :param entity: Entity :py:class:`model.Model` to persist.

        :returns: Resulting :py:class:`model.Key` from write operation. """

    _indexed_properties = self._pluck_indexed(entity)

    # reuse pipeline passed, if any
    if 'pipeline' in kwargs:
      pipeline = kwargs['pipeline']
      del kwargs['pipeline']
    else:
      pipeline = (
        self.channel(entity.kind()).pipeline(transaction=True))

    # provision ID early if there is none
    if not entity.key.id:
      entity.key.id = self.allocate_ids(entity.__keyclass__, entity.kind())

    with pipeline as pipe:

      # delegate write up the chain
      written_key = super(IndexedModelAdapter, self)._put(entity,
                                                        pipeline=pipe, **kwargs)

      # proxy to `generate_indexes` and write indexes
      origin, meta, property_map, graph = (
        self.generate_indexes(entity.key, entity, _indexed_properties))

      self.write_indexes((origin, meta, property_map), graph,
                          pipeline=pipe, **kwargs)

      # collapse pipelines
      pipe.execute()
      return written_key  # delegate up the chain for entity write

  @classmethod
  def put(cls, key, entity, model, pipeline=None):

    """ Persist an entity to storage in Redis.

        :param key: New (and potentially empty) :py:class:`model.Key` for
          ``entity``. Must be assigned an ``ID`` by the driver through
          :py:meth:`RedisAdapter.allocate_ids` in the case of an empty
          (non-deterministic) :py:class:`model.Key`.

        :param entity: Object entity :py:class:`model.Model` to persist in
          ``Redis``.

        :param model: Schema :py:class:`model.Model` associated with the target
          ``entity`` being persisted.

        :param pipeline: Existing pipeline of queued commands to append to, if
          applicable.

        :returns: Result of the lower-level write operation. """

    from canteen import model as _model

    # reduce entity to dictionary
    serialized = entity if isinstance(entity, dict) else (
      entity.to_dict(convert_datetime=False,
                     convert_keys=True,
                     convert_models=True))
    joined, flattened = key

    # clean key types
    _cleaned = {}
    for k, v in serialized.iteritems():
      prop = getattr(model, k)
      if isinstance(v, (datetime.date, datetime.time, datetime.datetime)):
        _cleaned[k] = v.isoformat()  # pragma: no cover
      else:
        _cleaned[k] = v

    # serialize + optionally compress
    serialized = cls.serializer.dumps(_cleaned)
    if cls.EngineConfig.compression:  # pragma: no cover
      compressed = cls.compressor.compress(serialized)

      if len(compressed) < len(serialized):
        # we saved space, store it compressed and it should uncompress on `get`
        serialized = compressed

    # toplevel_blob
    if cls.EngineConfig.mode == RedisMode.toplevel_blob:

      # delegate to redis client
      if cls.execute(*(
          cls.Operations.SET,
          flattened[1],
          joined,
          serialized), target=pipeline):
        entity._set_persisted(True)
        return entity.key
      else:  # pragma: no cover
        raise RuntimeError('Failed to write entity "%s" to key "%s".' % (
          str(entity), str(key) or '<none>'))

    ## need a serialized blob...

    ## hashkind_blob
    if cls.EngineConfig.mode == RedisMode.hashkind_blob:

      # generate kinded key and trim tail
      kinded = _model.Key(flattened[1]).flatten(True)
      tail = entity.key.flatten(True)[0].replace(kinded[0], '')

      # delegate to redis client
      if cls.execute(*(
        cls.Operations.HASH_SET,
        flattened[1],
        cls.encode_key(*kinded),
        cls.encode_key(tail, flattened),
        serialized), target=pipeline):
        entity._set_persisted(True)
        return entity.key
      else:  # pragma: no cover
        raise RuntimeError('Failed to write entity "%s" to key "%s".' % (
          str(entity), str(key) or '<none>'))

    ## hashkey_blob
    elif cls.EngineConfig.mode == RedisMode.hashkey_blob:

      # find entity group key
      root = (ancestor for ancestor in entity.key.ancestry).next().flatten(True)
      tail = entity.key.flatten(True)[0].replace(root[0], '') or '__root__'

      if cls.execute(*(
        cls.Operations.HASH_SET,
        flattened[1],
        cls.encode_key(*root),
        cls.encode_key(tail, flattened),
        serialized), target=pipeline):
        entity._set_persisted(True)
        return entity.key
      else:  # pragma: no cover
        raise RuntimeError('Failed to write entity "%s" to key "%s".' % (
          str(entity), str(key) or '<none>'))

    ## hashkey_hash
    elif cls.EngineConfig.mode == RedisMode.hashkey_hash:  # pragma: no cover

      raise NotImplementedError('Redis mode not implemented: "hashkey_hash".')

    raise NotImplementedError("Unknown storage mode: '%s'." % (
                              cls.EngineConfig.mode))  # pragma: no cover

    # @TODO: different storage internal modes

  # @TODO(sgammon): testing for ability to delete entities

  @classmethod
  def delete(cls, key, pipeline=None):

    """ Delete an entity by Key from Redis.

        :param key: Target :py:class:`model.Key`, whose associated
          :py:class:`model.Model` is being deleted.

        :returns: The result of the low-level delete operation. """

    from canteen import model

    # @TODO(sgammon): access to structured keys in adapters

    encoded, flattened = key
    try:
      joined, _ = model.Key.from_urlsafe(encoded).flatten(True)
    except TypeError:  # pragma: no cover
      joined = encoded
      encoded = cls.encode_key((joined, flattened))


    if cls.EngineConfig.mode == RedisMode.toplevel_blob:

      # delegate to redis client with encoded key
      return cls.execute(*(
        cls.Operations.DELETE,
        flattened[1],
        cls.encode_key(joined, flattened)), target=pipeline)

    elif cls.EngineConfig.mode == RedisMode.hashkind_blob:

      # generate kinded key and trim tail
      kinded = model.Key(flattened[1]).flatten(True)
      tail = joined.replace(kinded[0], '')

      # delegate to redis client
      return cls.execute(*(
        cls.Operations.HASH_DELETE,
        flattened[1],
        cls.encode_key(*kinded),
        cls.encode_key(tail, flattened)), target=pipeline)

    elif cls.EngineConfig.mode == RedisMode.hashkey_blob:

      # build key and extract group
      desired_key = model.Key.from_raw(joined)
      root = (ancestor for ancestor in desired_key.ancestry).next()
      tail = (
        desired_key.flatten(True)[0].replace(root.flatten(True)[0], '') or (
          '__root__'))

      return cls.execute(*(
        cls.Operations.HASH_DELETE,
          flattened[1],
          cls.encode_key(*root.flatten(True)),
          cls.encode_key(tail, flattened)), target=pipeline)

    elif cls.EngineConfig.mode == RedisMode.hashkey_hash:  # pragma: no cover

      raise NotImplementedError('Redis mode not implemented: "hashkey_hash".')

    raise NotImplementedError("Unknown storage mode: '%s'." % (
                              cls.EngineConfig.mode))  # pragma: no cover

  @classmethod
  def allocate_ids(cls, key_class, kind, count=1, pipeline=None):

    """ Allocate new :py:class:`model.Key` IDs up to ``count``. Allocated IDs
        are guaranteed not to be provisioned or otherwise used by the underlying
        persistence engine, and thus can be used for uniquely identifying
        non-deterministic data.

        :param key_class: Descendent of :py:class:`model.Key` to allocate IDs
          for.

        :param kind: String :py:class:`model.Model` kind name.

        :param count: The number of IDs to generate, which **must** be greater
          than 1. Defaults to ``1``.

        :raises ValueError: In the case the ``count`` is less than ``1``.

        :returns: If **only one** ID is requested, an **integer ID** suitable
          for use in a :py:class:`model.Key` directly. If **more than one** ID
          is requested, a **generator** is returned, which ``yields`` a set of
          provisioned integer IDs, each suitable for use in a
          :py:class:`model.Key` directly. """

    if not count:  # pragma: no cover
      raise ValueError("Cannot allocate less than 1 ID's.")

    # generate kinded key to resolve ID pointer
    kinded_key = key_class(kind)
    joined, flattened = kinded_key.flatten(True)

    if cls.EngineConfig.mode == RedisMode.toplevel_blob:
      key_root_id = cls._magic_separator.join([
        cls._meta_prefix, cls.encode_key(joined, flattened)])

      # increment by the amount desired
      value = cls.execute(*(
        cls.Operations.HASH_INCREMENT,
        kinded_key.kind,
        key_root_id,
        cls._id_prefix,
        count), target=pipeline)

    elif cls.EngineConfig.mode in (
      RedisMode.hashkind_blob,
      RedisMode.hashkey_blob):

      # store auto-increment for kind in kind's own hash at special field
      # ends up as `__meta__::id` or so
      tail = cls._magic_separator.join([cls._meta_prefix, 'id'])

      # delegate to redis client
      value = cls.execute(*(
        cls.Operations.HASH_INCREMENT,
        flattened[1],
        cls.encode_key(joined, flattened),
        cls.encode_key(tail, flattened),
        count), target=pipeline)

    elif cls.EngineConfig.mode == RedisMode.hashkey_hash:  # pragma: no cover

      raise NotImplementedError('Redis mode not implemented: "hashkey_hash".')

    else:  # pragma: no cover

      raise NotImplementedError("Unknown storage mode: '%s'." % (
                                cls.EngineConfig.mode))

    if count > 1:  # pragma: no cover
      def _generate_range():

        """ Generate a range of requested ID's.

            :yields: Each item in a set of provisioned integer IDs,
              suitable for use in a :py:class:`model.Key`. """

        bottom_range = (value - count)
        for i in xrange(bottom_range, value):
          yield i

      return _generate_range
    return value

  @classmethod
  def encode_key(cls, joined, flattened=None):  # pragma: no cover

    """ Encode a Key for storage in ``Redis``. Since we don't need to
        do anything fancy, just delegate this to the abstract (default)
        encoder, which is ``base64``.

        If :py:attr:`RedisEngine.EngineConfig.encoding` is disabled, this
        simply returns the ``joined`` :py:class:`model.Key` (for reference,
        see :py:meth:`model.Key.flatten`).

        :param joined: String-joined :py:class:`model.Key`.

        :param flattened: Tupled ("raw format") :py:class:`model.Key`.

        :returns: In the case that ``encoding`` is *on*, the encoded string
          :py:class:`model.Key`, suitable for storage in ``Redis``. Otherwise
          (``encoding`` is *off*), the cleartext ``joined`` key. """

    from canteen import model

    if isinstance(joined, model.Key): return joined.urlsafe()
    if cls.EngineConfig.encoding: return abstract._encoder(joined)
    return joined

  @classmethod
  def write_indexes(cls, w, g, pipeline=None, execute=True):

    """ Write a batch of index updates generated earlier via
        :py:meth:`RedisAdapter.generate_indexes`.

        :param w: Batch of writes to commit to ``Redis``.
        :param g: Batch of graph writes to commit to ``Redis``.

        :param pipeline: Current active pipeline of ``Redis`` commands to
          collapse and execute. Defaults to ``None``, which either returns the
          queued commands (if ``execute`` is ``False``) or a list of results
          from those commands (if ``execute`` is ``True``). Always returned
          if not ``None``, so that other calls can be chained.

        :param execute: Whether we should actually execute the writes, or just
          plan it and send it back. ``bool``, defaults to ``True``, which *does*
          execute the writes.

        :raises RuntimeError:

        :returns: ``pipeline`` if ``pipeline`` was not ``None``, or a ``tuple``
          of operation results if ``execute`` was ``True`` and ``pipeline`` was
          ``None``, or a tuple of plans that *would* be executed if ``pipeline``
           is ``None`` and ``execute`` is ``False``. """

    from .. import Vertex, Edge, VertexKey, EdgeKey

    origin, meta, property_map = w

    results, indexer_calls = [], []

    # resolve target (perhaps a pipeline?)
    if pipeline:  # pragma: no cover
      target = pipeline
    else:  # pragma: no cover
      target = cls.channel(cls._meta_prefix)

    handler, ekey_encoder, vkey_encoder = (
      cls.Operations.SET_ADD,
      cls._index_basetypes[EdgeKey],
      cls._index_basetypes[VertexKey])

    # write graph indexes
    for bundle in g:  # pragma: no cover

      bundle_args = []

      # one- or two-element tuples are simple indexes (and always edges)
      if 0 < len(bundle) < 3:
        bundle_args.append(Edge)
        bundle_args.append(cls._magic_separator.join(bundle))
        bundle_args.append(origin)

      # three-element tuples are encoded key indexes
      elif len(bundle) == 3:

        # encode key components
        _components = []
        for _item in bundle:
          if isinstance(_item, EdgeKey):
            _components.append(ekey_encoder(_item)[1])
          elif isinstance(_item, VertexKey):
            _components.append(vkey_encoder(_item)[1])
          elif isinstance(_item, basestring):
            _components.append(_item)
          else:  # pragma: no cover
            raise ValueError('Got invalid value in graph index bundle'
                             ' that was neither a `basestring` or `VertexKey`'
                             ' or `EdgeKey`. Instead, got: "%s"'
                             ' of type "%s".' % (repr(_item), type(_item)))

        # slice key and value into args
        gbase, gtoken, gtarget = tuple(_components)

        bundle_args.append(Vertex)
        bundle_args.append(cls._magic_separator.join((cls._graph_prefix,
                                                      gbase,
                                                      gtoken)))
        bundle_args.append(gtarget)

      # invalid indexer bundle
      else:  # pragma: no cover
        raise RuntimeError('Invalid graph index bundle: "%s".' % bundle)

      # build index key
      indexer_calls.append((handler, tuple(bundle_args), {'target': target}))

    # write meta and property indexes
    for btype, bundle in (('meta', meta), ('property', property_map)):

      # add meta indexes first
      for element in bundle:  # pragma: no cover

        # provision args, kwargs, and hash components containers
        args, kwargs, hash_c = [], {}, []

        if btype == 'meta':
          # meta indexes are always unicode
          converter, write = unicode, element
        else:
          # property indexes come through with a type converter
          converter, write = element

          # basestring is not allowed to be instantiated
          if converter is basestring: converter = cls.serializer.dumps

        ## Unpack index write
        if len(write) > 3:  # qualified value-key-mapping index

          # extract write, inflate
          index, path, value = write[0], write[1:-1], write[-1]
          hash_c.append(index)
          hash_c.append(cls._path_separator.join(path))
          hash_value = True  # add hashed value later

        elif len(write) == 3:  # value-key-mapping index

          # extract write, inflate
          index, path, value = write
          hash_c.append(index)
          hash_c.append(cls._path_separator.join(path))
          hash_value = True  # add hashed value later

        elif len(write) == 2:  # it's a qualified key index

          # extract write, inflate
          index, value = write
          hash_c.append(index)
          hash_value = True  # do not add hashed value later

        elif len(write) == 1:  # it's a simple key index

          # extract index, add value
          index, path, value = write[0], None, origin
          hash_c.append(index)
          hash_value = False  # do not add hashed value later

        else:
          raise ValueError('Invalid index write bundle: "%s".' % write)

        # resolve datatype of index
        if not isinstance(value, bool) and isinstance(value, _SERIES_BASETYPES):

          if converter is None:  # pragma: no cover
            raise RuntimeError('Illegal non-string value passed in'
                               ' for a `meta` index value.'
                               ' Write bundle: "%s".' % write)

          # convert things over to floats
          converter = lambda x: x
          if isinstance(value, (datetime.date, datetime.datetime)):
            converter = cls._index_basetypes[type(value)]
          elif isinstance(value, (int, long)):
            converter = float

          # time-based or number-like values are stored in sorted sets
          handler = cls.Operations.SORTED_ADD
          sanitized_value = converter(value)

          if isinstance(sanitized_value, tuple):
            magic_symbol, sanitized_value = sanitized_value
            hash_c.append(unicode(magic_symbol))
            args.append(sanitized_value)  # add calculated score to args
          else:
            args.append(sanitized_value)
          args.append(origin)  # add key to args

        else:

          # @TODO(sgammon): this can cause silent issues

          # everything else is stored unsorted
          handler = cls.Operations.SET_ADD

          if converter and value is not None:
            sanitized_value = converter(value)
          else:
            sanitized_value = value

          if hash_value:
            hash_c.append(sanitized_value)
          args.append(origin)

        # build index key
        indexer_calls.append((handler, tuple([
          None, cls._magic_separator.join(map(str, hash_c))] + args), {
            'target': target}))

    if execute:  # pragma: no cover
      for handler, hargs, hkwargs in indexer_calls:
        results.append(cls.execute(handler, *hargs, **hkwargs))

      if pipeline:
        return pipeline
      return results
    return indexer_calls  # pragma: no cover

  @classmethod
  def clean_indexes(cls, writes, pipeline=None):  # pragma: no cover

    """ Clean indexes and index entries matching a particular
        :py:class:`model.Key`, and generated via the adapter method
        :py:meth:`RedisAdapter.generate_indexes`.

      :param writes: Writes to clean up.

      :returns: ``None``. """

    return  # not currently implemented

  @classmethod
  def execute_query(cls, kind, spec, options, **kwargs):  # pragma: no cover

    """ Execute a :py:class:`model.Query` across one (or multiple) indexed
        properties.

        :param kind: Kind name (``str``) for which we are querying across, or
          ``None`` if this is a ``kindless`` query.

        :param spec: Tupled pair of ``filter`` and ``sort`` directives to apply
          to this :py:class:`Query` (:py:class:`query.Filter` and
          :py:class:`query.Sort` and their descendents, respectively), like
          ``(<filters>, <sorts>)``.

        :param options: Object descendent from, or directly instantiated as
          :py:class:`QueryOptions`, specifying options for the execution of
          this :py:class:`Query`.

        :param kwargs: Low-level options for handling this query, such as
          ``pipeline`` (for pipelining support) and ``execute`` (to trigger a
          buffer flush for a generated or constructed pipeline or operation
          buffer).

        :returns: Iterable (``list``) of matching :py:class:`model.Key` yielded
          by execution of the current :py:class:`Query`. Returns
          empty iterable (``[]``) in the case that no results could be
          found. """

    # @TODO(sgammon): desparately needs rewriting. absolute utter plebbery.

    from canteen import model
    from canteen.model import query

    # extract filter and sort directives and build ancestor
    filters, sorts = spec
    _data_frame = []  # allocate results window
    _base_kind = kind

    # calculate ancestry parent
    ancestry_parent = None
    if isinstance(options.ancestor, basestring):
      ancestry_parent = model.Key.from_urlsafe(options.ancestor)
    elif isinstance(options.ancestor, model.Key):
      ancestry_parent = options.ancestor
    elif isinstance(options.ancestor, model.Model):
      ancestry_parent = options.ancestor.key

    _and_filters, _or_filters, kinded_key = (
      [], [], model.Key(kind, parent=ancestry_parent))

    if ancestry_parent:
      filters.insert(0, query.KeyFilter(ancestry_parent,
                                     _type=query.KeyFilter.ANCESTOR))

    if not kind and not filters:  # it's a kindless query to start
      filters.append(query.KeyFilter(None))

    ## HUGE HACK: use generate_indexes to make index names.
    # fix this plz

    if kind and not filters:  # it's a vanilla kind query
      filters.append(query.KeyFilter(kind))

    _filters, _filter_i_lookup = {}, set()
    for _f in filters:

      # handle graph-based edge/neighbor filters first
      if isinstance(_f, query.EdgeFilter):

        # extract property values
        _data = _f.value.data if (
          isinstance(_f.value, model.Model._PropertyValue)) else _f.value

        # graph prefix and search key
        _index_key = [
          cls._graph_prefix,
          cls._index_basetypes[model.VertexKey](_data)[1]]

        # edge queries
        if _f.kind is _f.EDGES:

          # undirected edge queries
          if _f.tails is None:
            _index_key.append(cls._peers_token)

          else:
            # directed edge queries
            _index_key.append(cls._out_token if _f.tails else cls._in_token)

        # neighbor queries
        elif _f.kind is _f.NEIGHBORS:
          _index_key.append(cls._neighbors_token)

        else:  # pragma: no cover
          raise RuntimeError('Invalid `EdgeFilter` kind: "%s".' % _f.kind)

        # check for uniqueness and add to queued, unsorted filters
        _filter_key = ('S', cls._magic_separator.join(_index_key))
        if _filter_key not in _filter_i_lookup:
          _filter_i_lookup.add(_filter_key)
          _filters[_filter_key] = [(_f.operator, _f.value, _f.chain)]

      elif isinstance(_f, query.KeyFilter):

        # -- kind filters -- #
        if _f.kind is query.KeyFilter.KIND:

          ## kindless queries
          if _f.value is None:
            # query on main key index
            _filter_key = ('S', cls._key_prefix)

          ## kinded queries
          else:
            _filter_kind = _f.value.data

            if isinstance(_filter_kind, basestring) and _filter_kind in (
                  frozenset(('Edge', 'Vertex', 'Model'))):

              # we are querying for all [edges,vertexes,models]
              _filter_key = (
                'S', {
                  'Model': cls._key_prefix,
                  'Edge': cls._edge_prefix,
                  'Vertex': cls._vertex_prefix}.get(_filter_kind))

            else:
              # query on kind indexes
              _filter_key = (
                'S', cls._magic_separator.join((
                  cls._kind_prefix, _filter_kind)))

        # -- ancestry filters -- #
        elif _f.kind is query.KeyFilter.ANCESTOR:

          ## ancestor-less queries
          if _f.value is None:
            raise RuntimeError('Root entity filters are not yet supported'
                               ' in Redis.')

          ## ancestored queries
          else:
            # query on keygroups
            _filter_key = ('S', cls._magic_separator.join((cls._group_prefix,
                                                           _f.value.data)))

        # append key index merge
        if _filter_key not in _filter_i_lookup:
          _filter_i_lookup.add(_filter_key)
          _filters[_filter_key] = [(_f.EQUALS, _f.value, _f.chain)]

      # then handle property/meta filters, etc
      else:
        origin, meta, property_map, graph_indexes = (
          cls.generate_indexes(*(
            kinded_key, None, {_f.target.name: (_f.target, _f.value.data)})))

        for operation, index, config in cls.write_indexes(
              (origin, [], property_map), graph_indexes, execute=False):

          if operation == cls.Operations.SORTED_ADD:
            _flag, _index_key, value = 'Z', index[1], index[2]
          else:
            _flag, _index_key, value = 'S', index[1], index[2]

        if (_flag, _index_key) not in _filter_i_lookup:
          _filters[(_flag, _index_key)] = []
          _filter_i_lookup.add((_flag, _index_key))

        _filters[(_flag, _index_key)].append((_f.operator, value, _f.chain))

    # process sorted sets first: leads to lower cardinality
    sorted_indexes = dict([
      (index, _filters[index]) for index in (
        filter(lambda x: x[0] == 'Z', _filters.iterkeys()))])

    unsorted_indexes = dict([
      (index, _filters[index]) for index in (
        filter(lambda x: x[0] == 'S', _filters.iterkeys()))])

    if sorted_indexes:

      for prop, _directives in sorted_indexes.iteritems():

        _operator, _value, chain = _directives[0]

        if chain:
          for subquery in chain:
            if subquery.sub_operator is query.AND:
              _and_filters.append(subquery)
            if subquery.sub_operator is query.OR:
              _or_filters.append(subquery)

        # double-filters
        if len(_filters[prop]) == 2:

          # extract info
          _operators = [operator for operator, value in _directives]
          _values = [value for operator, value in _directives]
          _, prop = prop

          # special case: maybe we can do a sorted range request
          if (query.GREATER_THAN in _operators) or (
                  query.GREATER_THAN_EQUAL_TO in _operators):

            if (query.LESS_THAN in _operators) or (
                  query.LESS_THAN_EQUAL_TO in _operators):

              # range value query over sorted index
              greater, lesser = max(_values), min(_values)
              _data_frame.append(cls.execute(*(
                cls.Operations.SORTED_RANGE_BY_SCORE,
                None,
                prop,
                lesser,
                greater,
                options.offset,
                options.limit)))

              continue

        if len(_filters[prop]) == 1:  # single-filters

          # extract info
          _operator, _value = (
            ((operator, value) for (
                                 operator, value, chain) in _directives).next())
          _, prop = prop

          if _operator is query.EQUALS:

            # static value query over sorted index
            _data_frame.append(cls.execute(*(
              cls.Operations.SORTED_RANGE_BY_SCORE,
              None,
              prop,
              _value,
              _value)))

            continue

          elif _operator is query.LESS_THAN:

            # no lower bound
            _data_frame.append(cls.execute(
              cls.Operations.SORTED_RANGE_BY_SCORE,
              None,
              prop,
              '-inf',
              float(_value) if not (
                isinstance(_value, float)) else _value))

            continue

          elif _operator is query.GREATER_THAN:
            # no lower bound
            _data_frame.append(cls.execute(
              cls.Operations.SORTED_RANGE_BY_SCORE,
              None,
              prop,
              float(_value) if not (
                isinstance(_value, float)) else _value,
              '+inf'))

            continue

        ## @TODO(sgammon): build this query branch
        raise RuntimeError("Specified query is not yet supported.")

    if unsorted_indexes:

      _intersections = set()
      for prop, _directives in unsorted_indexes.iteritems():

        _operator, _value, chain = _directives[0]

        if chain:
          for subquery in chain:
            if subquery.sub_operator is query.AND:
              _and_filters.append(subquery)
            if subquery.sub_operator is query.OR:
              _or_filters.append(subquery)

        _flag, index = prop

        if _operator in (query.EQUALS, query.CONTAINS):
          _intersections.add(index)
        elif _operator is query.NOT_EQUALS:
          _and_filters.append(_f)
        else:
          # @TODO(sgammon): support this query branch
          raise RuntimeError('Specified query is not yet supported.')

      if (_or_filters or _and_filters) and not _data_frame:
        # couldn't resolve backing indexes - query is naked with and/or
        # (chained or not, doesn't matter, gotta start with all of that kind)
        _kinded_index_key = cls._magic_separator.join((cls._kind_prefix,
            (kind if isinstance(kind, basestring) else kind.kind())))
        _intersections.add(_kinded_index_key)

      # special case: only one unsorted set - pull content instead
      # of an intersection merge
      if _intersections and len(_intersections) == 1:
        _data_frame.append(cls.execute(*(
          cls.Operations.SET_MEMBERS,
          None,
          _intersections.pop())))

      # more than one intersection: do an `SINTER` call instead of `SMEMBERS`
      elif _intersections and len(_intersections) > 1:
        _data_frame.append(cls.execute(*(
          cls.Operations.SET_INTERSECT,
          None,
          _intersections)))

    if _data_frame:  # there were results, start merging
      _result_window = set()
      for frame in _data_frame:

        if not len(_result_window):
          _result_window = set(frame)
          continue  # initial frame: fill background

        _result_window &= (set(frame) if not isinstance(frame, set) else frame)
      matching_keys = (k for k in _result_window)
    else:
      matching_keys = []

    # if we're doing keys only, we're done
    if options.keys_only and not (_and_filters or _or_filters or sorts):

      _seen_results, results = 0, []
      for k in matching_keys:

        if 0 < options.limit <= _seen_results:
          break
        else:
          _seen_results += 1

          # @TODO(sgammon): unambiguous key classes
          vanilla = model.Key.from_urlsafe(k, _persisted=True)
          if vanilla.kind != _base_kind.kind():
            _base_kind = cls.registry.get(vanilla.kind, _base_kind)
            results.append(
              _base_kind.__keyclass__.from_urlsafe(k, _persisted=True))
          else:
            results.append(vanilla)
      return results

    result_entities, bundles = [], []  # otherwise, build entities and return

    # fill pipeline
    _queued = collections.deque()
    for key in matching_keys:

      decoded_k, _base_kind = (
        model.Key.from_urlsafe(key, _persisted=True), None)
      if not decoded_k.kind == kind.kind():
        _base_kind = cls.registry.get(kind.kind())
      if decoded_k.kind == kind.kind() or not _base_kind:
        _base_kind = kind

      if not _base_kind:  # pragma: no cover
        raise TypeError('Unknown model kind: "%s".' % decoded_k.kind)

      # @TODO(sgammon): make vertex/edge keys unambiguous
      decoded_k = _base_kind.__keyclass__.from_urlsafe(key)

      # queue fetch of key
      _queued.append(decoded_k)

      joined, flattened = decoded_k.flatten(True)
      bundles.append((cls.encode_key(joined, flattened), flattened))

    # execute pipeline, zip keys and build results
    if bundles:
      _seen_results = 0
      for entity in cls.get_multi(bundles):
        if not entity: continue  # skip entities that couldn't be found

        if _and_filters or _or_filters:
          if _and_filters and not all((
                  (_filter.match(entity) for _filter in _and_filters))):
            continue  # doesn't match one of the filters

          if _or_filters and not any((
                  (_filter.match(entity) for _filter in _or_filters))):
            continue  # doesn't match any of the `or` filters

        result_entities.append(entity.key if options.keys_only else (
                               entity))

        _seen_results += 1
        if 0 < options.limit <= _seen_results:
          break

      # prepare and collapse sort chain, if needed
      if sorts:
        if len(sorts) == 1:

          sorted_results, sort_chain, sort = [], sorted(
            result_entities, key=itemgetter(sorts[0].target.name)), sorts[0]

          # apply descending, but be careful about asc/dsc string sorts
          if ((sort.target.basetype in (basestring, unicode, str)) and (
                sort.operator is sort.ASCENDING) or (
                sort.operator is sort.DESCENDING) and (
                sort.target.basetype not in (basestring, unicode, str))):
            sort_chain = reversed(sort_chain)

          for entity in sort_chain:
            sorted_results.append(entity)
          return sorted_results

        else:
          # dammit, i guess collapse and apply
          raise RuntimeError('too many sorts :(')

    return result_entities
