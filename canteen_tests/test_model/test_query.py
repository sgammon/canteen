# -*- coding: utf-8 -*-

"""

  model query tests
  ~~~~~~~~~~~~~~~~~

  tests querying in canteen's model layer.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# canteen
from canteen import model
from canteen.model import query
from canteen.test import FrameworkTest

# inmemory adapter
from canteen_tests.test_adapters import test_abstract as abstract


## QueryTests
class QueryTests(FrameworkTest):

  """ Tests for `model.query.Query` and `model.query.QueryOptions`. """

  def test_construct(self):

    """ Test basic construction of a `model.Query` """

    assert hasattr(query, 'Query')
    assert query.Query
    assert query.Query()

  def test_options(self):

    """ Test basic construction of `query.QueryOptions` """

    assert hasattr(query, 'QueryOptions')
    assert query.QueryOptions()

  def test_options_invalid(self):

    """ Test setting an invalid setting on `QueryOptions` """

    options = query.QueryOptions()
    with self.assertRaises(AttributeError):
      options._set_option('make_me_dinner', True)

  def test_options_limit(self):

    """ Test the use of a query limit in `QueryOptions`  """

    assert query.QueryOptions(limit=50).limit == 50

  def test_options_offset(self):

    """ Test the use of a query offset in `QueryOptions` """

    assert query.QueryOptions(offset=50).offset == 50

  def test_options_ancestor(self):

    """ Test the use of a query ancestor in `QueryOptions` """

    assert query.QueryOptions(ancestor=model.Key('SampleModel', 'hi')).ancestor

  def test_options_overlay(self):

    """ Test overlaying one `QueryOptions` on another """

    left = query.QueryOptions(limit=50)
    right = query.QueryOptions(ancestor=model.Key('SampleModel', 'hi'))

    combined = left.overlay(right)
    assert combined.limit == 50
    assert combined.ancestor == model.Key('SampleModel', 'hi')

  def test_options_overlay_override(self):

    """ Test overlaying property overrides with `QueryOptions` """

    left = query.QueryOptions(limit=50)
    right = query.QueryOptions(limit=25,
                               ancestor=model.Key('SampleModel', 'hi'))

    overridden = left.overlay(right, override=True)
    assert overridden.limit == 25
    assert overridden.ancestor == model.Key('SampleModel', 'hi')

  def test_options_overlay_no_override(self):

    """ Test safely overlaying properties with `QueryOptions` """

    left = query.QueryOptions(limit=50)
    right = query.QueryOptions(limit=25,
                               ancestor=model.Key('SampleModel', 'hi'))

    overridden = left.overlay(right, override=False)
    assert overridden.limit == 50
    assert overridden.ancestor == model.Key('SampleModel', 'hi')

  def test_optioned_query(self):

    """ Test using `QueryOptions` with a `model.Query` """

    options = query.QueryOptions(limit=50,
                                 ancestor=model.Key('SampleModel', 'hi'))
    q = query.Query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key('SampleModel', 'hi')

  def test_interface_primitive_filter_objects(self):

    """ Test using primitive `query.Filter` objects in a `model.Query` """

    class SomeModel(model.Model):

        """ Some sample model """

        string = basestring
        integer = int

    filter_one = query.Filter(SomeModel.string, 'hi', operator=query.EQUALS)
    filter_two = query.Filter(SomeModel.integer, 5, operator=query.GREATER_THAN)

    q = SomeModel.query(filter_one, filter_two)

    assert len(q.filters) == 2
    assert filter_one in q.filters
    assert filter_two in q.filters

  def test_sort_pack(self):

    """ Test packing a `Sort` object into an opaque string """

    q = query.Sort(abstract.SampleModel.string)
    string = q.pack()

    assert ":" not in string

  def test_sort_pack_struct(self):

    """ Test packing a `Sort` object into a structure describing it """

    q = query.Sort(abstract.SampleModel.string)
    struct = q.pack(False)

    assert isinstance(struct, tuple)

  def test_interface_primitive_sort_objects(self):

    """ Test using primitive `query.Sort` objects in a `model.Query` """

    class SomeModel(model.Model):

        """ Some sample model """

        string = basestring
        integer = int

    sort_one = query.Sort(SomeModel.string, operator=query.ASCENDING)
    sort_two = query.Sort(SomeModel.integer, operator=query.DSC)

    q = SomeModel.query(sort_one, sort_two)

    assert len(q.sorts) == 2
    assert sort_one in q.sorts
    assert sort_two in q.sorts

  def test_interface_primitive_both_objects(self):

    """ Test primitive `query.Sort` inline with `query.Filter` objects """

    class SomeModel(model.Model):

        """ Some sample model """

        string = basestring
        integer = int

    filter_one = query.Filter(SomeModel.string, 'hi', operator=query.EQUALS)
    filter_two = query.Filter(SomeModel.integer, 5, operator=query.GREATER_THAN)
    sort_one = query.Sort(SomeModel.string, operator=query.ASCENDING)
    sort_two = query.Sort(SomeModel.integer, operator=query.DSC)

    q = SomeModel.query(filter_one, filter_two, sort_one, sort_two)

    assert len(q.filters) == 2
    assert filter_one in q.filters
    assert filter_two in q.filters

    assert len(q.sorts) == 2
    assert sort_one in q.sorts
    assert sort_two in q.sorts

  def test_interface_sort_default(self):

    """ Test specifying a (default-direction) `Sort` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.sort(-abstract.SampleModel.string)

    assert len(q.sorts) == 1
    assert q.sorts[0].operator == query.DESCENDING

  def test_interface_sort_ascending(self):

    """ Test specifying an ascending `Sort` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.sort(+abstract.SampleModel.string)

    assert len(q.sorts) == 1
    assert q.sorts[0].operator == query.ASCENDING

  def test_interface_sort_descending(self):

    """ Test specifying a descending `Sort` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.sort(-abstract.SampleModel.string)

    assert len(q.sorts) == 1
    assert q.sorts[0].operator == query.DESCENDING

  def test_interface_equality_filter(self):

    """ Test specifying an equality `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.string == 'sup')

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.EQUALS

  def test_interface_inequality_filter(self):

    """ Test specifying an inequality `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.string != 'sup')

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.NOT_EQUALS

  def test_interface_greater_than_filter(self):

    """ Test specifying a greater-than `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.integer > 5)

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.GREATER_THAN

  def test_interface_less_than_filter(self):

    """ Test specifying a less-than `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.integer < 5)

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.LESS_THAN

  def test_interface_greater_than_equal_to_filter(self):

    """ Test specifying a greater-than-equal-to `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.integer >= 5)

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.GREATER_THAN_EQUAL_TO

  def test_interface_less_than_equal_to_filter(self):

    """ Test specifying a less-than-equal-to `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.number <= 5)

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.LESS_THAN_EQUAL_TO

  def test_manual_filter_match(self):

    """ Test manually matching against a `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.number <= 5)
    matching_model = abstract.SampleModel(number=1, string='womp')

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.LESS_THAN_EQUAL_TO
    assert q.filters[0].match(matching_model)

    q = abstract.SampleModel.query(options=options)
    q.filter((abstract.SampleModel.number <= 5).AND((
        abstract.SampleModel.string == 'womp')))

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.LESS_THAN_EQUAL_TO
    assert q.filters[0].match(matching_model)

    q = abstract.SampleModel.query(options=options)
    q.filter((abstract.SampleModel.number <= 5).OR((
        abstract.SampleModel.string == 'womp')))

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.LESS_THAN_EQUAL_TO
    assert q.filters[0].match(matching_model)

  def test_manual_filter_match_value(self):

    """ Test manually matching a raw value against a `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.number <= 5)
    matching_model = abstract.SampleModel(number=1, string='womp')

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.LESS_THAN_EQUAL_TO
    assert q.filters[0].match(matching_model.number)

  def test_manual_filter_match_raw_entity(self):

    """ Test manually matching a raw entity against a `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.number <= 5)
    matching_model = abstract.SampleModel(number=1, string='womp')

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.LESS_THAN_EQUAL_TO
    assert q.filters[0].match(matching_model.to_dict())

  def test_sort_string_repr(self):

    """ Test the string representation for a `Sort` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.sort(-abstract.SampleModel.string)

    assert len(q.sorts) == 1
    assert q.sorts[0].operator == query.DESCENDING

    result = q.sorts[0].__repr__()
    assert 'Sort' in result
    assert 'DESCENDING' in result

  def test_filter_string_repr(self):

    """ Test the string representation for a `Filter` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    q = abstract.SampleModel.query(options=options)

    assert q.options.limit == 50
    assert q.options.ancestor == model.Key(abstract.SampleModel, 'hi')

    q.filter(abstract.SampleModel.integer <= 5)
    matching_model = abstract.SampleModel(integer=1)

    assert len(q.filters) == 1
    assert q.filters[0].operator == query.LESS_THAN_EQUAL_TO
    assert q.filters[0].match(matching_model)

    result = q.filters[0].__repr__()
    assert 'Filter' in result
    assert 'integer' in result

  def test_key_filter_invalid(self):

    """ Test `KeyFilter` with invalid values """

    with self.assertRaises(ValueError):
      query.KeyFilter(123)

  def test_filter_pack(self):

    """ Test packing a `Filter` object into an opaque string """

    from canteen import model

    q = query.Filter(abstract.SampleModel.string, "hithere")
    string = q.pack()

    assert ":" not in string

    q = query.Filter(abstract.SampleModel.string, None)
    string = q.pack()

    assert ":" not in string

    q = query.KeyFilter(model.Key("Hi", "sup"))
    string = q.pack()

    assert ":" not in string

    q = query.Filter(abstract.SampleModel.string, model.Key("Hi", "sup"))
    string = q.pack()

    assert ":" not in string

  def test_filter_pack_struct(self):

    """ Test packing a `Filter` object into a structure describing it """

    q = query.Filter(abstract.SampleModel.string, "hithere")
    struct = q.pack(False)

    assert isinstance(struct, tuple)

  def test_options_string_repr(self):

    """ Test the string representation for a `QueryOptions` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    result = options.__repr__()

    assert 'QueryOptions' in result
    assert 'limit' in result
    assert 'ancestor' in result

  def test_options_pack(self):

    """ Test packing a `QueryOptions` object into an opaque string """

    o = query.QueryOptions(limit=50, offset=10, keys_only=True)
    string = o.pack()

    assert ":" not in string

  def test_options_pack_struct(self):

    """ Test packing a `QueryOptions` object into a structure describing it """

    o = query.QueryOptions(limit=50, offset=10, keys_only=True)
    struct = o.pack(False)

    assert isinstance(struct, tuple)

  def test_query_pack(self):

    """ Test packing a `Query` object into an opaque string """

    o = query.QueryOptions(limit=50, offset=10, keys_only=True)
    q = query.Query(options=o)
    string = q.pack()

    assert ":" not in string

  def test_query_pack_struct(self):

    """ Test packing a `Query` object into a structure describing it """

    o = query.QueryOptions(limit=50, offset=10, keys_only=True)
    q = query.Query(options=o)
    struct = q.pack(False)

    assert isinstance(struct, tuple)

  def test_query_string_repr(self):

    """ Test the string representation for a `Query` """

    _ancestor = model.Key(abstract.SampleModel, 'hi')
    options = query.QueryOptions(limit=50, ancestor=_ancestor)
    _q = abstract.SampleModel.query(options=options)
    _q.filter(abstract.SampleModel.integer <= 5)
    _q.sort(+abstract.SampleModel.string)

    result = _q.__repr__()

    assert 'limit' in result
    assert 'ancestor' in result
    assert 'Sort' in result
    assert 'Filter' in result
    assert 'ASCENDING' in result
    assert '<=' in result

  def test_chained_construction(self):

    """ Test constructing a chained query with `Query` """

    class SomeModel(model.Model):

        """ Some sample model """

        string = basestring
        integer = int

    filter_one = query.Filter(SomeModel.string, 'hi', operator=query.EQUALS)
    filter_two = query.Filter(SomeModel.integer, 5,
                              operator=query.GREATER_THAN,
                              AND=(filter_one,))

    q = SomeModel.query(filter_one, filter_two)

    assert len(q.filters) == 2
    assert filter_one in q.filters
    assert filter_two in q.filters

    q = query.Query(filters=filter_one)

  def test_repeated_contains(self):

    """ Test constructing a CONTAINS query w/EQUALS on a repeated property """

    class SomeModel(model.Model):

        """ Some sample model """

        string = basestring, {'repeated': True}
        integer = int

    filter_one = query.Filter(SomeModel.string, 'hi', operator=query.EQUALS)
    q = SomeModel.query(filter_one)

    assert len(q.filters) == 1
    assert filter_one in q.filters
    assert filter_one.operator is query.CONTAINS
