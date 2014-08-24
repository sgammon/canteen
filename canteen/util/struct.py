# -*- coding: utf-8 -*-

'''

  datastructures
  ~~~~~~~~~~~~~~

  lightweight datastructures for use inside and outside
  :py:class:`canteen`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import abc

# canteen util
from . import decorators


class Sentinel(object):

  ''' Create a named sentinel object. '''

  name = None
  hash = None
  _falsy = False

  def __init__(self, name, falsy=False):

    ''' Construct a new ``Sentinel``, which is essentially just a symbolic
        object at a simple string name. Two ``Sentinel``s with the same name
        evaluate to be *equal* to each other.

        :param name: Simple string name for the new ``Sentinel``-to-be.

        :param falsy: Whether the resulting ``Sentinel`` object should evaluate
          as *falsy* (if it is to stand-in for ``None`` or ``False``, for
          instance). '''

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
_EMPTY, _TOMBSTONE = (
  Sentinel("EMPTY", True),
  Sentinel("TOMBSTONE", True)
)


class UtilStruct(object):

  ''' Abstract class for a utility object. '''

  __metaclass__ = abc.ABCMeta

  ## Init -- Accept structure fill
  def __new__(cls, *args, **kwargs):

    ''' Class constructor that enforces abstractness
        at the root of the class tree.

        :param *args:
        :param **kwargs:

        :raises NotImplementedError: If the root class
        :py:class:`UtilStruct` is constructed directly
        Otherwise, returns a new instance of the
        requested class. '''

    if cls.__name__ is 'UtilStruct':
      raise NotImplementedError('Cannot construct `UtilStruct` directly as'
                                ' it is an abstract class.')
    return object.__new__(cls, *args, **kwargs)

  @abc.abstractmethod
  def fillStructure(self, struct, case_sensitive=False, **kwargs):

    ''' Abstract method that fills a local object with data, usually
        from initialization.

        :param struct:
        :param case_sensitive:
        :param kwargs:

        :raises:
        :returns: '''

    raise NotImplementedError('`UtilStruct.fillStructure` is abstract and must'
                              ' be implemented by a subclass.')


class ObjectProxy(UtilStruct):

  ''' Same handy object as above, but stores the entries in an
      _entries attribute rather than the class dict.  '''

  _entries = _case_sensitive = None

  def __init__(self, struct=None, case_sensitive=False, **kwargs):

    ''' If handed a dictionary (or something) in init, send it to
        fillStructure (and do the same for kwargs).

        :param struct:
        :param case_sensitive:
        :param kwargs:

        :raises TypeError:

        :returns: '''

    self._entries, self._case_sensitive = {}, case_sensitive
    if struct:
      if kwargs: struct.update(kwargs)
      self.fillStructure(struct, case_sensitive=case_sensitive)

  def fillStructure(self, fill, case_sensitive=False, **kwargs):

    ''' If handed a dictionary, will fill self with
        those entries. Usually called from ``__init__``.

        :param fill: Structure to fill self with.

        :param case_sensitive: Whether we should
        initialize while ignoring case.

        :param kwargs: Keyword arguments to be applied
        to ``struct`` as override.

        :returns: ``self``. '''

    self.case_sensitive = case_sensitive
    if fill:
      if kwargs: fill.update(kwargs)
      for k, v in (fill.iteritems() if isinstance(fill, dict) else iter(fill)):
        self._entries[self.i_filter(k)] = v
    return self

  def __getitem__(self, name):

    ''' 'x = struct[name]' override.

        :param name:
        :raises KeyError:
        :returns: '''

    filtered = self.i_filter(name)
    if filtered not in self._entries:
      raise KeyError("Cannot locate name '%s'"
                     " in ObjectProxy '%s'." % (name, self))
    return self._entries[filtered]

  def __getattr__(self, name):

    ''' 'x = struct.name' override.

        :param name:
        :raises AttributeError
        :returns: '''

    filtered = self.i_filter(name)
    if filtered not in self._entries:
      raise AttributeError("Could not find the attribute '%s'"
                           " on the specified ObjectProxy." % name)
    return self._entries[filtered]

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

  ''' Same handy object as `ObjectProxy`, but
      allows appending things at runtime. '''

  def __setitem__(self, name, value):

    ''' 'struct[name] = x' override.

        :param name:
        :param value:
        :returns: '''

    self._entries[name] = value

  def __setattr__(self, name, value):

    ''' 'struct.name = x' override.

        :param name:
        :param value:
        :returns: '''

    if name in ('_entries', '_case_sensitive', '__slots__'):
      return object.__setattr__(self, name, value)
    self._entries[name] = value

  def __delattr__(self, name):

    ''' 'del struct.name' override.

        :param name:
        :raises AttributeError:
        :returns: '''

    if self.i_filter(name) not in self._entries:
      raise AttributeError("Could not find the entry '%s'"
                           " on the specified ObjectProxy." % name)
    del self._entries[self.i_filter(name)]

  def __delitem__(self, name):

    ''' 'del struct[name]' override.

        :param name:
        :raises KeyError:
        :returns: '''

    if self.i_filter(name) not in self._entries:
      raise KeyError("Could not find the entry '%s'"
                     " on the specified ObjectProxy." % name)
    del self._entries[self.i_filter(name)]


class CallbackProxy(ObjectProxy):

  ''' Handy little object that takes a dict and makes
      it accessible via var[item], but returns the
      result of an invoked ``callback(item)``. '''

  _entries = None  # cached entries
  callback = None  # callback func

  def __init__(self, callback, struct={}, **kwargs):

    ''' Map the callback and fillStructure if we
        get one via `struct`.

        :param callback:
        :param struct:
        :param kwargs:
        :returns: '''

    self.callback = callback

    self._entries = struct
    if kwargs: self._entries.update(kwargs)

  def __getitem__(self, name):

    ''' 'x = struct[name]' override.

        :param name:
        :raises KeyError:
        :returns: '''

    if self._entries and name not in self._entries:
      raise KeyError("Could not retrieve item '%s'"
                     " from CallbackProxy '%s'." % (name, self))
    return self.callback((self._entries.get(name) if self._entries else name))

  def __getattr__(self, name):

    ''' 'x = struct.name' override.

        :param name:
        :raises AttributeError:
        :returns: '''

    if self._entries and name not in self._entries:
      raise AttributeError("CallbackProxy could not resolve entry '%s'." % name)
    return self.callback((self._entries.get(name) if self._entries else name))

  # `struct()` override
  __call__ = lambda self, *args, **kwargs: self.callback(*args, **kwargs)


class ObjectDictBridge(UtilStruct):

  ''' Treat an object like a dict, or an object! Assign an object
      with `ObjectDictBridge(<object>)`. Then access properties
      with `bridge[item]` or `bridge.item`. '''

  target = None  # target object

  def __init__(self, target_object):

    ''' constructor.

        :param target_object:
        :returns: '''

    super(ObjectDictBridge, self).__setattr__('target', target_object)

  # `obj[item]` syntax
  __getitem__ = lambda self, name: getattr(self.target, name)
  __setitem__ = lambda self, name: setattr(self.target, name)
  __delitem__ = lambda self, name: delattr(self.target, name)

  # `obj.item` syntax
  __getattr__ = lambda self, name: getattr(self.target, name)
  __setattr__ = lambda self, name: setattr(self.target, name)
  __delattr__ = lambda self, name: delattr(self.target, name)

  # contains override
  __contains__ = lambda self, name: bool(getattr(self.target, name, False))

  # dict-style `get()`
  get = lambda self, name, default=None: getattr(self.target, name, default)


@decorators.singleton
class BidirectionalEnum(object):

  ''' Small and simple datastructure for mapping
      static flags to smaller values. '''

  class __metaclass__(abc.ABCMeta):

    ''' Metaclass for property-gather-enabled classes. '''

    def __new__(cls, name, chain, _map):

      ''' Read mapped properties, store on the
          object, along with a reverse mapping.

          :param name:
          :param chain:
          :param _map:
          :returns: '''

      # Init calculated data attributes
      _map['_pmap'] = {}
      _map['_plookup'] = []

      # Define __contains__ proxy
      def _contains(proxied_o, flag_or_value):

        ''' Bidirectionally-compatible __contains__
            replacement.

            :param proxied_o:
            :param flag_or_value:
            :returns: '''

        return flag_or_value in proxied_o._plookup

      # Define __getitem__ proxy
      def _getitem(proxied_o, fragment):

        ''' Attempt to resolve the fragment by a
            forward, then reverse resolution chain.

            :param proxied_o:
            :param fragment:
            :returns: '''

        if proxied_o.__contains__(fragment):
          return proxied_o._pmap.get(fragment)

      # Define __setitem__ proxy
      def _setitem(proxied_o, n, v):

        ''' Block setitem calls, because this is a
            complicated object that is supposed
            to be a modelling tool only.

            :param proxied_o:
            :param n:
            :param v:
            :raises NotImplementedError: '''

        raise NotImplementedError('Not implemented')

      def _iter(proxied_cls):

        ''' Iterate over all enumerated values.

            :returns: '''

        for k, v in proxied_cls._plookup:
          yield k, v

      # Map properties into data and lookup attributes
      map(lambda x: ([
        _map['_pmap'].update(dict(x)),
        _map['_plookup'].append([x[0][0], x[1][0]])]),
        (((a, v), (v, a)) for a, v in _map.items() if not a.startswith('_')))

      if '__getitem__' not in _map:
        _map['__getitem__'] = _getitem
      if '__setitem__' not in _map:
        _map['__setitem__'] = _setitem
      if '__contains__' not in _map:
        _map['__contains__'] = _contains
      if '__iter__' not in _map:
        _map['__iter__'] = _iter

      return super(cls, cls).__new__(cls, name, chain, _map)

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
