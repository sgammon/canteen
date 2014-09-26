# -*- coding: utf-8 -*-

"""

  datastructures
  ~~~~~~~~~~~~~~

  lightweight datastructures for use inside and outside
  :py:class:`canteen`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import abc

# canteen util
from . import decorators


## Globals
_ENUM_TYPES = int, long, float, basestring, bool


class Sentinel(object):

  """ Create a named sentinel object. """

  name, hash, _falsy = None, None, False

  def __init__(self, name, falsy=False):

    """ Construct a new ``Sentinel``, which is essentially just a symbolic
        object at a simple string name. Two ``Sentinel``s with the same name
        evaluate to be *equal* to each other.

        :param name: Simple string name for the new ``Sentinel``-to-be.

        :param falsy: Whether the resulting ``Sentinel`` object should evaluate
          as *falsy* (if it is to stand-in for ``None`` or ``False``, for
          instance). """

    self.name, self.hash, self._falsy = (
      name, int((''.join(str(ord(c)) for c in name))), falsy)

  # hash value for this sentinel
  __hash__ = lambda self: self.hash

  # equality comparator
  __eq__ = lambda self, other: (
    isinstance(other, self.__class__) and other.hash == self.hash)

  # string representation
  __repr__ = lambda self: '<Sentinel "%s">' % self.name

  # stringification value
  __str__ = __unicode__ = lambda self: self.name

  # falsyness
  __nonzero__ = lambda self: (not self._falsy)


# Sentinels
EMPTY, _TOMBSTONE = (
  Sentinel("EMPTY", True),
  Sentinel("TOMBSTONE", True))


class UtilStruct(object):

  """ Abstract class for a utility object. """

  __metaclass__ = abc.ABCMeta

  ## Init -- Accept structure fill
  def __new__(cls, *args, **kwargs):

    """ Class constructor that enforces abstractness at the root of the class
        tree.

        :param *args:
        :param **kwargs:

        :raises NotImplementedError: If the root class :py:class:`UtilStruct` is
          constructed directly. Otherwise, returns a new instance of the
          requested class. """

    if cls.__name__ is 'UtilStruct':
      raise NotImplementedError('Cannot construct `UtilStruct` directly as'
                                ' it is an abstract class.')
    return object.__new__(cls, *args, **kwargs)

  @abc.abstractmethod
  def fillStructure(self, struct, case_sensitive=False, **kwargs):

    """ Abstract method that fills a local object with data, usually from
        initialization.

        :param struct:
        :param case_sensitive:
        :param kwargs:

        :raises:
        :returns: """

    raise NotImplementedError('`UtilStruct.fillStructure` is abstract and must'
                              ' be implemented by a subclass.')


class ObjectProxy(UtilStruct):

  """ Same handy object as above, but stores the entries in an _entries
      attribute rather than the class dict.  """

  _entries = _case_sensitive = None

  def __init__(self, struct=None, case_sensitive=False, **kwargs):

    """ If handed a dictionary (or something) in init, send it to fillStructure
        (and do the same for kwargs).

        :param struct:
        :param case_sensitive:
        :param kwargs:

        :raises TypeError:

        :returns: """

    self._entries, self._case_sensitive = {}, case_sensitive
    if struct:
      if kwargs: struct.update(kwargs)
      self.fillStructure(struct, case_sensitive=case_sensitive)

  def fillStructure(self, fill, case_sensitive=False, **kwargs):

    """ If handed a dictionary, will fill self with those entries. Usually
        called from ``__init__``.

        :param fill: Structure to fill self with.

        :param case_sensitive: Whether we should initialize while ignoring case.

        :param kwargs: Keyword arguments to be applied to ``struct`` as
          override.

        :returns: ``self``. """

    self._case_sensitive = case_sensitive
    if fill:
      if kwargs: fill.update(kwargs)
      for k, v in (fill.iteritems() if isinstance(fill, dict) else iter(fill)):
        self._entries[self.i_filter(k)] = v
    return self

  def __getitem__(self, name):

    """ 'x = struct[name]' override.

        :param name:
        :raises KeyError:
        :returns: """

    filtered = self.i_filter(name)
    if filtered not in self._entries and name not in self._entries:
      raise KeyError("Cannot locate name '%s'"
                     " in ObjectProxy '%s'." % (name, self))
    return self._entries.get(filtered, self._entries.get(name))

  def __getattr__(self, name):

    """ 'x = struct.name' override.

        :param name:
        :raises AttributeError
        :returns: """

    filtered = self.i_filter(name)
    if filtered not in self._entries and name not in self._entries:
      raise AttributeError("Could not find the attribute '%s'"
                           " on the specified ObjectProxy." % name)
    return self._entries.get(filtered, self._entries.get(name))

  # filter for case sensitivity
  i_filter = lambda self, target: (
    (self._case_sensitive and target) or str(target).lower())

  # contains override
  __contains__ = contains = lambda self, name: (
    self.i_filter(name) in self._entries)

  # dict-style buffered access
  keys = lambda self: self._entries.keys()
  values = lambda self: self._entries.values()
  items = lambda self: self._entries.items()

  # dict-style streaming access
  iterkeys = lambda self: self._entries.iterkeys()
  itervalues = lambda self: self._entries.itervalues()
  iteritems = lambda self: self._entries.iteritems()


class WritableObjectProxy(ObjectProxy):

  """ Same handy object as `ObjectProxy`, but allows appending things at
      runtime. """

  def __setitem__(self, name, value):

    """ 'struct[name] = x' override.

        :param name:
        :param value:
        :returns: """

    self._entries[name] = value

  def __setattr__(self, name, value):

    """ 'struct.name = x' override.

        :param name:
        :param value:
        :returns: """

    if name in ('_entries', '_case_sensitive', '__slots__'):
      return object.__setattr__(self, name, value)
    self._entries[name] = value

  def __delattr__(self, name):

    """ 'del struct.name' override.

        :param name:
        :raises AttributeError:
        :returns: """

    if self.i_filter(name) not in self._entries:
      raise AttributeError("Could not find the entry '%s'"
                           " on the specified ObjectProxy." % name)
    del self._entries[self.i_filter(name)]

  def __delitem__(self, name):

    """ 'del struct[name]' override.

        :param name:
        :raises KeyError:
        :returns: """

    if self.i_filter(name) not in self._entries:
      raise KeyError("Could not find the entry '%s'"
                     " on the specified ObjectProxy." % name)
    del self._entries[self.i_filter(name)]


class CallbackProxy(ObjectProxy):

  """ Handy little object that takes a dict and makes it accessible via
      var[item], but returns the result of an invoked ``callback(item)``. """

  _entries = None  # cached entries
  callback = None  # callback func

  # noinspection PyMissingConstructor
  def __init__(self, callback, struct=None, **kwargs):

    """ Map the callback and fillStructure if we get one via `struct`.

        :param callback: Callable to produce return values, given the ``item``
          or ``attr`` desired. If this ``CallbackProxy`` has a set of registered
          ``self._entries``, and the requested ``item`` or ``attr`` is valid,
          the value at ``item`` or ``attr`` in ``self._entries`` will be passed
          as the first and only argument to ``callback`` when looking for a
          return value. If this ``CallbackProxy`` is unregistered, the desired
          ``item`` or ``attr`` name is passed as the first and only argument to
          ``callback``.

        :param struct: Structure (``dict``) of items to register in this
          ``CallbackProxy``'s local ``self._entries`` registry. If this
          structure is provided, it will be validated against for ``item`` or
          ``attr`` requests, and will be handed to the ``callback`` function
          as described above.

        :param **kwargs: ``key=value`` pairs to override in ``struct`` before
          registering in ``self._entries``. """

    struct = struct or {}
    self.callback = callback

    self._entries = struct
    if kwargs: self._entries.update(kwargs)

  def __getitem__(self, item):

    """ 'x = struct[item]' override.

        :param item: Item to fetch via ``self.callback``. If there are
          registered entries on the local ``CallbackProxy``, ``item`` must be
          present as a key, and the value at ``item`` is passed to the local
          ``self.callback`` for resolving a value.

        :raises KeyError: Raised if this ``CallbackProxy`` has registered
          ``self._entries`` and ``item`` is not present as a key. ``KeyError``s
          raised from ``self.callback`` are also bubbled.

        :returns: Result of ``self.callback(self._entries[item])`` if this
          ``CallbackProxy`` has registered ``self._entries``, or the result of
           ``self.callback(item)`` if there are no registered
           ``self._entries``. """

    if self._entries and item not in self._entries:
      raise KeyError("Could not retrieve item '%s'"
                     " from CallbackProxy '%s'." % (item, self))
    return self.callback((self._entries.get(item) if self._entries else item))

  def __getattr__(self, attr):

    """ 'x = struct.attr' override.

        :param attr: String attribute name to fetch from this ``CallbackProxy``,
          either via the result of ``self.callback(self._entries[attr])`` if
          there are registered ``self._entries`` or otherwise the result of
          ``self.callback(attr)``.

        :raises AttributeError: Raised if this ``CallbackProxy`` has registered
          ``self._entries`` and ``item`` is not present as a key.
          ``AttributeError``s raised from ``self.callback`` are also bubbled.

        :returns: Result of the ``callback`` dispatch as described above. """

    if self._entries and attr not in self._entries:
      raise AttributeError("CallbackProxy could not resolve entry '%s'." % attr)
    return self.callback((self._entries.get(attr) if self._entries else attr))

  def __contains__(self, item):

    """ 'x in struct' override.

       :param item: Item to check the local container for.

       :return: Whether or not ``item`` is held by ``self._entries``, or
         ``False`` if it could not be found (or if this ``CallbackProxy`` has no
         registered ``self._entries`` table). """

    return self._entries and item in self._entries

  # `struct()` override
  __call__ = lambda self, *args, **kwargs: self.callback(*args, **kwargs)


class BidirectionalEnum(object):

  """ Small and simple datastructure for mapping static names to symbolic
      values. Interoperable with the RPC and model layers. """

  __singleton__, __slots__ = True, tuple()

  class __metaclass__(type):

    """ Metaclass for property-gather-enabled classes. """

    def __new__(mcs, name, chain, _map):

      """ Read mapped properties, store on the object, along with a reverse
          mapping.

          :param name: Name of the ``BidirectionalEnum`` subtype to factory.
          :param chain: Inheritance chain for target subtype.
          :param _map: ``dict`` map of ``key = value`` attribute pairs.

          :raises RuntimeError: If a non-unique ``key`` or ``value`` is given
            as part of the ``BidirectionalEnum``-to-be's ``map``.

          :returns: Constructed ``BidirectionalEnum`` subclass. """

      # init calculated data attributes
      _pmap, _keys, _plookup = (
          _map['_pmap'], _map['_keys'], _map['_plookup']) = (
            {}, [], set())

      # set class-level enum properties
      for key, value in _map.iteritems():
        if not key.startswith('_') and isinstance(value, _ENUM_TYPES):
          if value in _plookup:  # pragma: no cover
            raise RuntimeError('Cannot map non-unique (double-validated)'
                               ' `BidirectionalEnum` value %s.' % value)
          if key in _plookup:  # pragma: no cover
            raise RuntimeError('Cannot map non-unique (double-validated)'
                               ' `BidirectionalEnum` key %s.' % value)

          # things look good: add the value
          _keys.append(key)
          _pmap[key] = value
          _pmap[value] = key
          _plookup.add(key)
          _plookup.add(value)

      _map['_keys'] = tuple(_keys)
      return type.__new__(mcs, name, chain, _map)

    def __iter__(cls):

      """ Iterate over all enumerated values.

         :returns: ``(k, v)`` tuples for each enumerated item and value, one at
          a time. """

      for k in cls._keys:
        yield k, getattr(cls, k)

    def __getitem__(cls, item):

      """ Fetch an item from the local ``BidirectionalEnum`` (forward resolve).

          :raises KeyError: If ``item`` is not a valid item registered on the
            local ``BidirectionalEnum``.

          :returns: Bound value at the (forward-resolved) item on the local
            ``BidirectionalEnum``. """

      return cls._pmap[item]

    def __contains__(cls, item):

      """ Check if an ``item`` is a registered member or value of the local
          ``BidirectionalEnum``.

          :param item: Item to check for membership against the local enum.

          :return: ``bool`` - ``True`` if ``item`` is a valid member with a
            bound value retrievable via item or attribute syntax or a value with
            a bound key retreivable via ``reverse_resolve``, otherwise
            ``False``. """

      return item in cls._plookup

    def __setitem__(cls, item, value):

      """ Disallow writing to items registered in the ``BidirectionalEnum``,
          as it is an immutable type.

          :param item: Item to write.
          :param value: Value to write at ``item``.

          :raises NotImplementedError: Always, as ``BidirectionalEnum`` is an
            immutable type. """

      raise NotImplementedError('`%s` is an immutable type'
                                ' and cannot be written to with item'
                                ' syntax. ' % cls.__name__)

    def __setattr__(cls, attr, value):

      """ Disallow writing to attributes registered in the ``BidirectionalEnum``,
          as it is an immutable type.

          :param attr: Attribute to write.
          :param value: Value to write at ``attr``.

          :raises NotImplementedError: Always, as ``BidirectionalEnum`` is an
            immutable type. """

      raise NotImplementedError('`%s` is an immutable type'
                                ' and cannot be written to with attribute'
                                ' syntax. ' % cls.__name__)

  def __new__(cls):

    """ Disallow direct construction of ``BidirectionalEnum`` objects.

        :raises TypeError: ``BidirectionalEnum`` is both an abstract class
          (itself) and an object that is always used as its type. Thus, objects
          of ``BidirectionalEnum`` are not allowed to be created and attempts
          to do so always result in ``TypeError``s. """

    raise TypeError('`%s` objects are abstract'
                    ' and only usable as type objects.' % cls.__name__)

  # forward and reverse resolve
  reverse_resolve = (
    classmethod(lambda cls, code: cls._pmap.get(code, False)))
  forward_resolve = resolve = (
    classmethod(lambda cls, flag: cls.__getattr__(flag, False)))

  # serialization and string repr
  __json__ = classmethod(lambda cls: cls.__serialize__())
  __serialize__ = (
    classmethod(lambda cls: dict(((k, v) for k, v in cls._plookup if not (
      k.startswith('_'))))))

  __repr__ = classmethod(lambda cls: ('::'.join([
      "<%s" % cls.__name__,
      ','.join([
        block for block in (
          '='.join([str(k), str(v)]) for k, v in cls.__serialize__().items())]),
      "BiDirectional>"])))
