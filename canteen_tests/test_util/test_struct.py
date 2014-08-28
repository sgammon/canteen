# -*- coding: utf-8 -*-

'''

  struct tests
  ~~~~~~~~~~~~

  tests for canteen's data structures utilities.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# testing
from canteen import test

# utils
from canteen.util import struct


class BaseUtilTests(test.FrameworkTest):

  ''' Tests toplevel stuff on :py:mod:`canteen.util`. '''

  def test_exports(self):

    ''' Test that `canteen.util` exports expected things. '''

    assert hasattr(struct, 'EMPTY')
    assert hasattr(struct, '_TOMBSTONE')


class SentinelTests(test.FrameworkTest):

  ''' Tests :py:class:`canteen.util.struct.Sentinel`,
      which represents a simple singleton sentinel
      value.

      Sentinels are kind of like The Highlander... '''

  def test_existence(self):

    ''' Test basic existence of `util.struct.Sentinel`. '''

    assert hasattr(struct, 'Sentinel')

  def test_construct(self):

    ''' Test basic functionality of `util.struct.Sentinel`. '''

    SAMPLE = struct.Sentinel('SAMPLE')
    assert SAMPLE.name == "SAMPLE"

  def test_equality(self):

    ''' Test basic equality comparison for `util.struct.Sentinel`. '''

    SAMPLE = struct.Sentinel('SAMPLE')
    assert SAMPLE.name == "SAMPLE"

    SAMPLE2 = struct.Sentinel('SAMPLE')
    assert SAMPLE == SAMPLE2

  def test_repr(self):

    ''' Test basic string representation of a `util.struct.Sentinel`. '''

    SAMPLE = struct.Sentinel('SAMPLE')
    assert 'SAMPLE' in str(SAMPLE)

  def test_falsy(self):

    ''' Test ability to set a Sentinel as falsy. '''

    BAD = struct.Sentinel('BAD', falsy=True)
    assert not BAD

  def test_not_falsy(self):

    ''' Test ability to set a Sentinel as truthy. '''

    GOOD = struct.Sentinel('GOOD', falsy=False)
    assert GOOD


class UtilStructTests(test.FrameworkTest):

  ''' Tests :py:class:`util.struct.UtilStruct`,
      which is used as a base class for utility
      data structures. '''

  def test_construct(self):

    ''' Test that `UtilStruct` is abstract. '''

    with self.assertRaises(NotImplementedError):
      struct.UtilStruct()

  def test_fillstruct_abstract(self):

    ''' Test that `UtilStruct.fillStructure is abstract. '''

    with self.assertRaises(TypeError):

      class UtilStructBadImplementor(struct.UtilStruct):

        ''' Bad implementor of `UtilStruct` that
            should always raise a `TypeError` upon
            instantiation. '''

        def i_am_not_fill_struct(self):

          ''' I am not `fillStruct`. '''

          return False

      UtilStructBadImplementor()

    with self.assertRaises(NotImplementedError):

      class UtilStructBadSuper(struct.UtilStruct):

        ''' Bad implementor of `UtilStruct` that
            should always raise a `NotImplementedError`
            because of invalid super access. '''

        def fillStructure(self, _struct, case_sensitive=False, **kwargs):

          ''' I am an invalid `fillStruct`. '''

          return super(UtilStructBadSuper, self).fillStructure(_struct, case_sensitive, **kwargs)

      UtilStructBadSuper().fillStructure({'blab': 'blab'})


class ObjectProxyTests(test.FrameworkTest):

  ''' Tests :py:class:`util.struct.ObjectProxy`,
      which makes a ``dict``-like object usable
      via attribute syntax. '''

  def test_construct(self):

    ''' Test that `util.ObjectProxy` can be constructed. '''

    # basic construction test
    st = struct.ObjectProxy()

    # construction test with struct
    st_struct = struct.ObjectProxy({
      'hi': True,
      'iam': False,
      'astruct': None
    })

    # construction test with kwargs
    st_kwargs = struct.ObjectProxy(hi=1, iam=2, astruct=3)

    # construction test with struct + kwargs
    st_both = struct.ObjectProxy({
      'hi': True,
      'iam': False,
      'astruct': None
    }, hi=1, iam=2)

  def test_fill_case_sensitive(self):

    ''' Test that `util.ObjectProxy` can be case sensitive. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None
    }, case_sensitive=True)

    assert st_struct.HelloThere is True
    assert not hasattr(st_struct, 'hellothere')
    assert 'HelloThere' in st_struct
    assert 'hellothere' not in st_struct
    assert 'idonotexist' not in st_struct
    assert 'IDoNotExist' not in st_struct

  def test_fill_case_insensitive(self):

    ''' Test that `util.ObjectProxy` can be case insensitive. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None
    }, case_sensitive=False)

    assert st_struct.HelloThere is True
    assert st_struct.hellothere is True
    assert 'HelloThere' in st_struct
    assert 'hellothere' in st_struct
    assert 'idonotexist' not in st_struct

  def test_getitem(self):

    ''' Test that `util.ObjectProxy` can be used with getitem syntax. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None
    }, case_sensitive=False)

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

    ''' Test that `util.ObjectProxy` can be used with getitem syntax. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None
    }, case_sensitive=False)

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

    ''' Test buffered iteration with `util.ObjectProxy.keys`. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None
    }, case_sensitive=True)

    ref = ('HelloThere', 'IamA', 'StRuct')
    for key in st_struct.keys():
      assert key in ref

  def test_iterkeys(self):

    ''' Test streaming iteration with `util.ObjectProxy.iterkeys`. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None
    }, case_sensitive=True)

    ref = ('HelloThere', 'IamA', 'StRuct')
    for key in st_struct.iterkeys():
      assert key in ref

    assert isinstance(st_struct.iterkeys(), {}.iterkeys().__class__)

  def test_values(self):

    ''' Test buffered iteration with `util.ObjectProxy.values`. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': 1,
      'IamA': 2,
      'StRuct': 3
    })

    ref = (1, 2, 3)
    for val in st_struct.values():
      assert val in ref

  def test_itervalues(self):

    ''' Test streaming iteration with `util.ObjectProxy.itervalues`. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': 1,
      'IamA': 2,
      'StRuct': 3
    })

    ref = (1, 2, 3)
    for val in st_struct.itervalues():
      assert val in ref

    assert isinstance(st_struct.itervalues(), {}.itervalues().__class__)

  def test_items(self):

    ''' Test buffered iteration with `util.ObjectProxy.items`. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None
    }, case_sensitive=True)

    ref = {'HelloThere': True, 'IamA': False, 'StRuct': None}
    for key, value in st_struct.items():
      assert ref[key] == value

  def test_iteritems(self):

    ''' Test streaming iteration with `util.ObjectProxy.iteritems`. '''

    st_struct = struct.ObjectProxy({
      'HelloThere': True,
      'IamA': False,
      'StRuct': None
    }, case_sensitive=True)

    ref = {'HelloThere': True, 'IamA': False, 'StRuct': None}
    for key, value in st_struct.iteritems():
      assert ref[key] == value

    assert isinstance(st_struct.iteritems(), {}.iteritems().__class__)


class WritableObjectProxyTests(test.FrameworkTest):

  ''' Tests :py:class:`util.struct.WritableObjectProxy`,
      which is like :py:class:`util.struct.ObjectProxy`
      but allows writes at runtime. '''

  def test_setitem(self):

    ''' Test that `util.WritableObjectProxy` can be used with setitem syntax. '''

    st_struct = struct.WritableObjectProxy()
    st_struct['hi'] = True

    assert 'hi' in st_struct
    assert st_struct['hi'] is True

  def test_setattr(self):

    ''' Test that `util.WritableObjectProxy` can be used with setattr syntax. '''

    st_struct = struct.WritableObjectProxy()
    st_struct.hi = True

    assert 'hi' in st_struct
    assert st_struct.hi is True

  def test_delitem(self):

    ''' Test that `util.WritableObjectProxy` can be used with delitem syntax. '''

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

    ''' Test that `util.WritableObjectProxy` can be used with delattr syntax. '''

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
