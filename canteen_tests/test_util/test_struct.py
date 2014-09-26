# -*- coding: utf-8 -*-

"""

  struct tests
  ~~~~~~~~~~~~

  tests for canteen's data structures utilities.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# testing
from canteen import test

# utils
from canteen.util import struct


class BaseUtilTests(test.FrameworkTest):

  """ Tests toplevel stuff on :py:mod:`canteen.util`. """

  def test_exports(self):

    """ Test that `canteen.util` exports expected things """

    assert hasattr(struct, 'EMPTY')
    assert hasattr(struct, '_TOMBSTONE')


class SentinelTests(test.FrameworkTest):

  """ Tests :py:class:`canteen.util.struct.Sentinel`, which represents a simple
      singleton sentinel value.

      Sentinels are kind of like The Highlander... """

  def test_existence(self):

    """ Test basic existence of `util.struct.Sentinel` """

    assert hasattr(struct, 'Sentinel')

  def test_construct(self):

    """ Test basic functionality of `util.struct.Sentinel` """

    SAMPLE = struct.Sentinel('SAMPLE')
    assert SAMPLE.name == "SAMPLE"

  def test_equality(self):

    """ Test basic equality comparison for `util.struct.Sentinel` """

    SAMPLE = struct.Sentinel('SAMPLE')
    assert SAMPLE.name == "SAMPLE"

    SAMPLE2 = struct.Sentinel('SAMPLE')
    assert SAMPLE == SAMPLE2

  def test_repr(self):

    """ Test basic string representation of a `util.struct.Sentinel` """

    SAMPLE = struct.Sentinel('SAMPLE')
    assert 'SAMPLE' in str(SAMPLE)

  def test_falsy(self):

    """ Test ability to set a Sentinel as falsy. """

    BAD = struct.Sentinel('BAD', falsy=True)
    assert not BAD

  def test_not_falsy(self):

    """ Test ability to set a Sentinel as truthy. """

    GOOD = struct.Sentinel('GOOD')
    assert GOOD


class UtilStructTests(test.FrameworkTest):

  """ Tests :py:class:`util.struct.UtilStruct`, which is used as a base class
      for utility data structures. """

  def test_construct(self):

    """ Test that `UtilStruct` is abstract """

    with self.assertRaises(NotImplementedError):
      struct.UtilStruct()

  def test_fillstruct_abstract(self):

    """ Test that `UtilStruct.fillStructure is abstract """

    with self.assertRaises(TypeError):


      class UtilStructBadImplementor(struct.UtilStruct):

        """ Bad implementor of `UtilStruct` that should always raise a
            `TypeError` upon instantiation. """

        def i_am_not_fill_struct(self):

          """ I am not `fillStruct`. """

          return False  # pragma: no cover

      UtilStructBadImplementor()

    with self.assertRaises(NotImplementedError):

      class UtilStructBadSuper(struct.UtilStruct):

        """ Bad implementor of `UtilStruct` that should always raise a
            `NotImplementedError` because of invalid super access. """

        def fillStructure(self, _struct, case_sensitive=False, **kwargs):

          """ I am an invalid `fillStruct`. """

          _s = super(UtilStructBadSuper, self)
          _s.fillStructure(*(_struct, case_sensitive), **kwargs)

      UtilStructBadSuper().fillStructure({'blab': 'blab'})


class ObjectProxyTests(test.FrameworkTest):

  """ Tests :py:class:`util.struct.ObjectProxy`, which makes a ``dict``-like
      object usable via attribute syntax. """

  def test_construct(self):

    """ Test that `util.ObjectProxy` can be constructed. """

    # basic construction test
    st = struct.ObjectProxy()

    # construction test with struct
    st_struct = struct.ObjectProxy({
      'hi': True,
      'iam': False,
      'astruct': None})

    # construction test with kwargs
    st_kwargs = struct.ObjectProxy(hi=1, iam=2, astruct=3)

    # construction test with struct + kwargs
    st_both = struct.ObjectProxy({
      'hi': True,
      'iam': False,
      'astruct': None}, hi=1, iam=2)

  def test_fill_case_sensitive(self):

    """ Test that `util.ObjectProxy` can be case sensitive. """

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None}, case_sensitive=True)

    assert st_struct.HelloThere is True
    assert not hasattr(st_struct, 'hellothere')
    assert 'HelloThere' in st_struct
    assert 'hellothere' not in st_struct
    assert 'idonotexist' not in st_struct
    assert 'IDoNotExist' not in st_struct

  def test_fill_case_insensitive(self):

    """ Test that `util.ObjectProxy` can be case insensitive. """

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None}, case_sensitive=False)

    assert st_struct.HelloThere is True
    assert st_struct.hellothere is True
    assert 'HelloThere' in st_struct
    assert 'hellothere' in st_struct
    assert 'idonotexist' not in st_struct

  def test_getitem(self):

    """ Test that `util.ObjectProxy` can be used with getitem syntax. """

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None}, case_sensitive=False)

    assert st_struct['HelloThere'] is True
    assert st_struct['hellothere'] is True
    assert 'HelloThere' in st_struct
    assert 'hellothere' in st_struct
    assert 'idonotexist' not in st_struct

    # try invalid names
    with self.assertRaises(KeyError):
      st_struct['IDoNotExist']
    with self.assertRaises(KeyError):
      st_struct['idonotexist']

  def test_getattr(self):

    """ Test that `util.ObjectProxy` can be used with getitem syntax. """

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None}, case_sensitive=False)

    assert st_struct.HelloThere is True
    assert st_struct.hellothere is True
    assert 'HelloThere' in st_struct
    assert 'hellothere' in st_struct
    assert 'idonotexist' not in st_struct

    # try invalid names
    with self.assertRaises(AttributeError):
      st_struct.idonotexist
    with self.assertRaises(AttributeError):
      st_struct.IDoNotExist

    # test special attributes
    assert st_struct._case_sensitive is False
    assert isinstance(st_struct._entries, dict)

  def test_keys(self):

    """ Test buffered iteration with `util.ObjectProxy.keys`. """

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None}, case_sensitive=True)

    ref = ('HelloThere', 'IamA', 'StRuct')
    for key in st_struct.keys():
      assert key in ref

  def test_iterkeys(self):

    """ Test streaming iteration with `util.ObjectProxy.iterkeys`. """

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None}, case_sensitive=True)

    ref = ('HelloThere', 'IamA', 'StRuct')
    for key in st_struct.iterkeys():
      assert key in ref

    assert isinstance(st_struct.iterkeys(), {}.iterkeys().__class__)

  def test_values(self):

    """ Test buffered iteration with `util.ObjectProxy.values`. """

    st_struct = struct.ObjectProxy({
      'HelloThere': 1,
      'IamA': 2,
      'StRuct': 3})

    ref = (1, 2, 3)
    for val in st_struct.values():
      assert val in ref

  def test_itervalues(self):

    """ Test streaming iteration with `util.ObjectProxy.itervalues`. """

    st_struct = struct.ObjectProxy({
      'HelloThere': 1,
      'IamA': 2,
      'StRuct': 3})

    ref = (1, 2, 3)
    for val in st_struct.itervalues():
      assert val in ref

    assert isinstance(st_struct.itervalues(), {}.itervalues().__class__)

  def test_items(self):

    """ Test buffered iteration with `util.ObjectProxy.items`. """

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None}, case_sensitive=True)

    ref = {'HelloThere': True, 'IamA': False, 'StRuct': None}
    for key, value in st_struct.items():
      assert ref[key] == value

  def test_iteritems(self):

    """ Test streaming iteration with `util.ObjectProxy.iteritems`. """

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None}, case_sensitive=True)

    ref = {'HelloThere': True, 'IamA': False, 'StRuct': None}
    for key, value in st_struct.iteritems():
      assert ref[key] == value

    assert isinstance(st_struct.iteritems(), {}.iteritems().__class__)


class WritableObjectProxyTests(test.FrameworkTest):

  """ Tests :py:class:`util.struct.WritableObjectProxy`,
      which is like :py:class:`util.struct.ObjectProxy`
      but allows writes at runtime. """

  def test_setitem(self):

    """ Test that `util.WritableObjectProxy` can be used with setitem syntax """

    st_struct = struct.WritableObjectProxy()
    st_struct['hi'] = True

    assert 'hi' in st_struct
    assert st_struct['hi'] is True

  def test_setattr(self):

    """ Test that `util.WritableObjectProxy` can be used with setattr syntax """

    st_struct = struct.WritableObjectProxy()
    st_struct.hi = True

    assert 'hi' in st_struct
    assert st_struct.hi is True

  def test_delitem(self):

    """ Test that `util.WritableObjectProxy` can be used with delitem syntax """

    st_struct = struct.WritableObjectProxy()
    st_struct['hi'] = True
    st_struct['bye'] = False

    assert st_struct['hi'] is True
    assert st_struct['bye'] is False

    del st_struct['bye']

    assert 'bye' not in st_struct
    with self.assertRaises(KeyError):
      st_struct['bye']

    # try deleting an invalid item
    with self.assertRaises(KeyError):
      del st_struct['i_was_never_here_lol']

  def test_delattr(self):

    """ Test that `util.WritableObjectProxy` can be used with delattr syntax """

    st_struct = struct.WritableObjectProxy()
    st_struct.hi = True
    st_struct.bye = False

    assert st_struct.hi is True
    assert st_struct.bye is False

    del st_struct.bye

    assert 'bye' not in st_struct
    with self.assertRaises(AttributeError):
      st_struct.bye

    # try deleting an invalid attr
    with self.assertRaises(AttributeError):
      del st_struct.i_was_never_here_lol


class CallbackProxy(test.FrameworkTest):

  """ Tests :py:class:`util.struct.CallbackProxy`, which dispatches a callable
      to satisfy calls via entries based either on a known set of keys or a
      direct call to the callable with the desired attribute. """

  def test_construct_keys(self):

    """ Test constructing a `CallbackProxy` with registered keys """

    addone = lambda key: key + 1
    _struct = {
        'one': 0,
        'two': 1}

    proxy = struct.CallbackProxy(addone, _struct)

    # proxies with structs can be used with `in`
    assert 'one' in proxy
    assert 'two' in proxy
    assert proxy['one'] is 1
    assert proxy['two'] is 2

    return proxy

  def test_construct_keys_merge(self):

    """ Test merging registered keys passed to `CallbackProxy` """

    addone = lambda key: key + 1
    _struct = {
        'one': 0,
        'two': 1}

    proxy = struct.CallbackProxy(addone, _struct, two=4, three=3)

    assert proxy['one'] == 1
    assert proxy['two'] == 5  # because we overrode it
    assert proxy['three'] == 4  # because we added is

  def test_construct_nokeys(self):

    """ Test constructing a `CallbackProxy` with unregistered keys """

    addhi = lambda attr: 'hi' + attr
    proxy = struct.CallbackProxy(addhi)

    assert proxy['one'] == 'hione'
    assert proxy['two'] == 'hitwo'

    return proxy

  def test_valid_getattr_with_keys(self):

    """ Test getting a valid attr from a `CallbackProxy` with keys """

    proxy = self.test_construct_keys()
    assert proxy.one == 1
    assert proxy.two == 2

  def test_invalid_getattr_with_keys(self):

    """ Test getting an invalid attr from a `CallbackProxy` with keys """

    proxy = self.test_construct_keys()
    assert proxy.one == 1
    assert proxy.two == 2
    with self.assertRaises(AttributeError):
      assert proxy.three

  def test_valid_getattr_with_nokeys(self):

    """ Test getting a valid attr from a `CallbackProxy` with no keys """

    proxy = self.test_construct_nokeys()
    assert proxy.one == 'hione'
    assert proxy.two == 'hitwo'
    assert proxy.blab == 'hiblab'

  def test_invalid_getattr_with_nokeys(self):

    """ Test getting an invalid attr from a `CallbackProxy` with no keys """

    def _callback(request):

      """ Conditionally raise an ``AttributeError``. """

      if request is 'woops':
        raise AttributeError('Don\'t ask for woops')
      return 'blab' + request

    proxy = struct.CallbackProxy(_callback)
    assert proxy.one == 'blabone'
    assert proxy.two == 'blabtwo'
    assert proxy.blab == ('blab' * 2)

    with self.assertRaises(AttributeError):
      assert proxy.woops

  def test_valid_getitem_with_keys(self):

    """ Test getting a valid item from a `CallbackProxy` with keys """

    proxy = self.test_construct_keys()
    assert proxy['one'] == 1
    assert proxy['two'] == 2

  def test_invalid_getitem_with_keys(self):

    """ Test getting an invalid item from a `CallbackProxy` with keys """

    proxy = self.test_construct_keys()
    assert proxy['one'] == 1
    assert proxy['two'] == 2
    with self.assertRaises(KeyError):
      assert proxy['three']

  def test_valid_getitem_with_nokeys(self):

    """ Test getting a valid item from a `CallbackProxy` with no keys """

    proxy = self.test_construct_nokeys()
    assert proxy['one'] == 'hione'
    assert proxy['two'] == 'hitwo'
    assert proxy['blab'] == 'hiblab'

  def test_invalid_getitem_with_nokeys(self):

    """ Test getting an invalid item from a `CallbackProxy` with no keys """

    def _callback(request):

      """ Conditionally raise an ``KeyError``. """

      if request is 'woops':
        raise KeyError('Don\'t ask for woops')
      return 'blab' + request

    proxy = struct.CallbackProxy(_callback)
    assert proxy['one'] == 'blabone'
    assert proxy['two'] == 'blabtwo'
    assert proxy['blab'] == ('blab' * 2)

    with self.assertRaises(KeyError):
      assert proxy['woops']


class BidirectionalEnumTests(test.FrameworkTest):

  """ Tests the utility structure :py:class:`BidirectionalEnum`, which makes
      enumeration structures that map keys to values and values to keys. """

  def test_construct(self):

    """ Test constructing a `BidirectionalEnum` """

    class Colors(struct.BidirectionalEnum):

      """ Enumerates pretty colors. """

      BLUE = 0x0
      RED = 0x1
      GREEN = 0x2

    return Colors

  def test_abstract(self):

    """ Test abstractness of `BidirectionalEnum` """

    with self.assertRaises(TypeError):
      struct.BidirectionalEnum()

  def test_contains(self):

    """ Test `x in y` syntax against `BidirectionalEnum` """

    enum = self.test_construct()
    assert 'BLUE' in enum
    assert 'RED' in enum
    assert 'GREEN' in enum
    assert 'BLACK' not in enum
    assert 'GRAY' not in enum

    # should work in reverse too
    assert 0x0 in enum
    assert 0x1 in enum
    assert 0x2 in enum
    assert 0x3 not in enum
    assert 0x4 not in enum

  def test_getattr(self):

    """ Test `x.y` syntax against `BidirectionalEnum` """

    enum = self.test_construct()
    assert enum.BLUE is enum.BLUE is 0x0
    assert enum.RED is enum.RED is 0x1
    assert enum.GREEN is enum.GREEN is 0x2

    with self.assertRaises(AttributeError):
      assert enum.BLACK

  def test_getitem(self):

    """ Test `x[y]` syntax against `BidirectionalEnum` """

    enum = self.test_construct()
    assert enum['BLUE'] is enum['BLUE'] is 0x0
    assert enum['RED'] is enum['RED'] is 0x1
    assert enum['GREEN'] is enum['GREEN'] is 0x2

    # reverse-resolve fallback should be supported
    assert enum[0x0] == 'BLUE'
    assert enum[0x1] == 'RED'
    assert enum[0x2] == 'GREEN'

    with self.assertRaises(KeyError):
      assert enum['BLACK']

  def test_immutable(self):

    """ Test `BidirectionalEnum` for immutability """

    enum = self.test_construct()

    # disallow new properties
    with self.assertRaises(NotImplementedError):
     enum['BLACK'] = 0x5

    with self.assertRaises(NotImplementedError):
      enum.BLACK = 0x5

    # disallow overwrites too
    with self.assertRaises(NotImplementedError):
      enum['GREEN'] = 0x5

    with self.assertRaises(NotImplementedError):
      enum.GREEN = 0x5

    # make sure nothing changed
    assert enum['GREEN'] is enum.GREEN is 0x2

  def test_reverse_resolve(self):

    """ Test reverse-resolving a key from a value with a `BidirectionalEnum` """

    enum = self.test_construct()

    assert enum.reverse_resolve(0x0) == 'BLUE'
    assert enum.reverse_resolve(0x1) == 'RED'
    assert enum.reverse_resolve(0x2) == 'GREEN'

    # reverse-resolves fail softly
    assert not enum.reverse_resolve(0x3)
    assert not enum.reverse_resolve(0x3)

  def test_iter(self):

    """ Test iteration against `BidirectionalEnum` """

    enum = self.test_construct()

    _struct = {
        'BLUE': 0x0,
        'RED': 0x1,
        'GREEN': 0x2}

    for key, value in enum:
      assert key in _struct
      assert _struct[key] is value
      _struct[key] = True

    assert all(_struct.itervalues())  # make sure all values touched
