# -*- coding: utf-8 -*-

'''

  canteen datastructures
  ~~~~~~~~~~~~~~~~~~~~~~

  lightweight datastructures for use inside and outside
  :py:class:`canteen`.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# Base Imports
import abc
import logging


class Sentinel(object):

  ''' Create a named sentinel object. '''

  name = None
  _falsy = False

  def __init__(self, name, falsy=False):

    ''' Construct a new sentinel.

      :param name:
      :param falsy:
      :returns: '''

    self.name, self._falsy = name, falsy

  def __repr__(self):

    ''' Represent this sentinel as a string.

      :returns: '''

    return '<Sentinel "%s">' % self.name

  def __nonzero__(self):

    ''' Test whether this sentinel is falsy.

      :returns: '''

    return (not self._falsy)


# Sentinels
_EMPTY, _TOMBSTONE = Sentinel("EMPTY", True), Sentinel("TOMBSTONE", True)


class UtilStruct(object):

  ''' Abstract class for a utility object. '''

  ## Init -- Accept structure fill
  def __init__(self, struct=None, case_sensitive=True, **kwargs):

    ''' If handed a dictionary (or something) in init, send it to
      fillStructure (and do the same for kwargs).

      :param struct:
      :param case_sensitive:
      :param kwargs:
      :raises TypeError:
      :returns: '''

    try:
      if struct is not None:
        self.fillStructure(struct, case_sensitive=case_sensitive)
      if len(kwargs) > 0:
        self.fillStructure(case_sensitive=case_sensitive, **kwargs)
    except TypeError:
      logging.critical('Type error encountered when trying to fillStructure.')
      logging.critical('Current struct: "%s".' % self)
      logging.critical('Target struct: "%s".' % struct)


class ObjectProxy(UtilStruct):

  ''' Same handy object as above, but stores the entries in an
    _entries attribute rather than the class dict.  '''

  _entries = {}
  i_filter = lambda _, k: k

  def __init__(self, fill=None, case_sensitive=True, **kwargs):

    ''' If handed a dictionary or kwargs, fill _entries with e[k] = v.
      A list will do the same and be interpreted as a list of tuples in (k, v) format.

      :param fill:
      :param case_sensitive:
      :param kwargs:
      :returns: '''

    if case_sensitive is False:
      self.i_filter = lambda k: str(k).lower()
    if fill is not None:
      if isinstance(fill, dict):
        for k, v in fill.iteritems():
          if case_sensitive is False:
            k = str(k).lower()
          self._entries[k] = v
      elif isinstance(fill, list):
        for k, v in fill:
          if case_sensitive is False:
            k = str(k).lower()
          self._entries[k] = v
    if kwargs:
      for k, v in kwargs.iteritems():
        if case_sensitive is False:
          k = str(k).lower()
        self._entries[k] = v

  def __getitem__(self, name):

    ''' 'x = struct[name]' override.

      :param name:
      :raises KeyError:
      :returns: '''

    if self.i_filter(name) not in self._entries:
      raise KeyError("Cannot locate name '%s' in ObjectProxy '%s'." % (name, self))
    return self._entries[self.i_filter(name)]

  def __delitem__(self, name):

    ''' 'del struct[name]' override.

      :param name:
      :raises KeyError:
      :returns: '''

    if self.i_filter(name) not in self._entries:
      raise KeyError("Could not find the entry '%s' on the specified ObjectProxy." % name)
    del self._entries[self.i_filter(name)]

  def __getattr__(self, name):

    ''' 'x = struct.name' override.

      :param name:
      :raises AttributeError
      :returns: '''

    if self.i_filter(name) not in self._entries:
      raise AttributeError("Could not find the attribute '%s' on the specified ObjectProxy." % name)
    return self._entries[self.i_filter(name)]

  def __contains__(self, name):

    ''' 'x in struct' override.

      :param name:
      :returns: '''

    return self.i_filter(name) in self._entries

  def __delattr__(self, name):

    ''' 'del struct.name' override.

      :param name:
      :raises AttributeError:
      :returns: '''

    if self.i_filter(name) not in self._entries:
      raise AttributeError("Could not find the entry '%s' on the specified ObjectProxy." % name)
    del self._entries[self.i_filter(name)]

  def keys(self):

    ''' return all keys in this struct.

      :returns: '''

    return self._entries.keys()

  def values(self):

    ''' return all values in this struct.

      :returns: '''

    self._entries.values()

  ## Utiliy Methods
  def items(self):

    ''' return all (k, v) pairs in this struct.

      :returns: '''

    return self._entries.items()


class WritableObjectProxy(ObjectProxy):

  ''' Same handy object as `ObjectProxy`, but allows appending things at runtime. '''

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

    self._entries[name] = value


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

    if struct is not None:
      self._entries = struct
    else:
      if kwargs:
        self._entries = dict([i for i in struct.iteritems()] + [i for i in kwargs.iteritems()])

  def __getitem__(self, name):

    ''' 'x = struct[name]' override.

      :param name:
      :raises KeyError:
      :returns: '''

    if self._entries:
      if name not in self._entries:
        raise KeyError("Could not retrieve item '%s' from CallbackProxy '%s'." % (name, self))
      return self.callback(self._entries.get(name))
    return self.callback(name)

  def __getattr__(self, name):

    ''' 'x = struct.name' override.

      :param name:
      :raises AttributeError:
      :returns: '''

    if self._entries:
      if not name or (name not in self._entries):
        raise AttributeError("CallbackProxy could not resolve entry '%s'." % name)
      return self.callback(self._entries.get(name))
    return self.callback(name)

  def __call__(self, *args, **kwargs):

    ''' 'struct()' override.

      :returns: '''

    return self.callback(*args, **kwargs)


class ObjectDictBridge(UtilStruct):

  ''' Treat an object like a dict, or an object! Assign an object
    with `ObjectDictBridge(<object>)`. Then access properties
    with `bridge[item]` or `bridge.item`. '''

  target = None  # target object

  def __init__(self, target_object=None):

    ''' constructor.

      :param target_object:
      :returns: '''

    super(ObjectDictBridge, self).__setattr__('target', target_object)

  def __getitem__(self, name):

    ''' 'x = struct[name]' override.

      :param name:
      :raise KeyError:
      :returns: '''

    if self.target is not None:
      try:
        return getattr(self.target, name)
      except AttributeError, e:
        raise KeyError(str(e))
    else:
      raise KeyError('No object target set for ObjectDictBridge.')

  def __setitem__(self, name):

    ''' 'struct[name] = x' override.

      :param name:
      :raises KeyError:
      :returns: '''

    if self.target is not None:
      try:
        return setattr(self.target, name)
      except Exception, e:
        raise e
    else:
      raise KeyError('No object target set for ObjectDictBridge.')

  def __delitem__(self, name):

    ''' 'del struct[name]' override.

      :param name:
      :raises KeyError:
      :raises AttributeError:
      :returns: '''

    if self.target is not None:
      try:
        return delattr(self.target, name)
      except Exception, e:
        raise e
    else:
      raise KeyError('No object target set for ObjectDictBridge.')

  def __getattr__(self, name):

    ''' 'x = struct.name' override.

      :param name:
      :raises KeyError:
      :raises AttributeError:
      :returns: '''

    if self.target is not None:
      try:
        return getattr(self.target, name)
      except Exception, e:
        raise e
    else:
      raise KeyError('No object target set for ObjectDictBridge.')

  def __setattr__(self, name):

    ''' 'struct.name = x' override.

      :param name:
      :raises KeyError:
      :raises AttributeError:
      :returns: '''

    if self.target is not None:
      try:
        return setattr(self.target, name)
      except Exception, e:
        raise e
    else:
      raise KeyError('No object target set for ObjectDictBridge.')

  def __delattr__(self, name):

    ''' 'del struct.name' override.

      :param name:
      :raises KeyError:
      :raises AttributeError:
      :returns: '''

    if self.target is not None:
      try:
        return delattr(self.target, name)
      except Exception, e:
        raise e
    else:
      raise KeyError('No object target set for ObjectDictBridge.')

  def __contains__(self, name):

    ''' Indicates whether this ObjectDictBridge
      contains the given key.

      :param name:
      :returns: '''

    try:
      getattr(self.target, name)
    except AttributeError:
      return False
    return True

  def get(self, name, default_value=None):

    ''' dict-like safe get (`obj.get(name, default)`).

      :param name:
      :param default_value:
      :returns: '''

    try:
      return getattr(self.target, name)
    except:
      return default_value
    return default_value


class BidirectionalEnum(object):

  ''' Small and simple datastructure for mapping
    static flags to smaller values. '''

  __singleton__ = True

  class __metaclass__(abc.ABCMeta):

    ''' Metaclass for property-gather-enabled classes. '''

    def __new__(cls, name, chain, mappings):

      ''' Read mapped properties, store on the
        object, along with a reverse mapping.

        :param name:
        :param chain:
        :param mappings:
        :returns: '''

      if name == 'ProxiedStructure':
        return type(name, chain, mappings)

      # Init calculated data attributes
      mappings['_pmap'] = {}
      mappings['_plookup'] = []

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

      # Map properties into data and lookup attributes
      map(lambda x: [mappings['_pmap'].update(dict(x)), mappings['_plookup'].append([x[0][0], x[1][0]])],
        (((attr, value), (value, attr)) for attr, value in mappings.items() if not attr.startswith('_')))

      if '__getitem__' not in mappings:
        mappings['__getitem__'] = _getitem
      if '__setitem__' not in mappings:
        mappings['__setitem__'] = _setitem
      if '__contains__' not in mappings:
        mappings['__contains__'] = _contains

      return super(cls, cls).__new__(cls, name, chain, mappings)

  @classmethod
  def reverse_resolve(cls, code):

    ''' Resolve a mapping, by it's integer/string code.

      :param code:
      :returns: '''

    if code in cls._pmap:
      return cls._pmap[code]
    return False

  @classmethod
  def forward_resolve(cls, flag):

    ''' Resolve a mapping, by it's string property name.

      :param flag:
      :returns: '''

    if flag in cls._pmap:
      return cls.__getattr__(flag)
    return False

  @classmethod
  def resolve(cls, flag): return cls.forward_resolve(flag)

  @classmethod
  def __serialize__(cls):

    ''' Flatten down into a structure suitable for
      storage/transport.

      :returns: '''

    return dict([(k, v) for k, v in dir(cls) if not k.startswith('_')])

  @classmethod
  def __json__(cls):

    ''' Flatten down and serialize into JSON.

      :returns: '''

    return cls.__serialize__()

  @classmethod
  def __repr__(cls):

    ''' Display a string representation of
      a flattened self.

      :returns: '''

    return '::'.join([
      "<%s" % self.__class__.__name__,
      ','.join([
        block for block in ('='.join([str(k), str(v)]) for k, v in cls.__serialize__().items())]),
      "BiDirectional>"
      ])