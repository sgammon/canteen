# -*- coding: utf-8 -*-

'''

  model queries
  ~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

'''


__version__ = 'v5'


# stdlib
import abc
import operator

# canteen utils
from canteen.util import struct as datastructures


## Globals / Constants

# Filter components
_TARGET_KEY = datastructures.Sentinel('KEY')
PROPERTY = datastructures.Sentinel('PROPERTY')
KEY_KIND = datastructures.Sentinel('KEY_KIND')
KEY_ANCESTOR = datastructures.Sentinel('KEY_ANCESTOR')

# Sort directions
ASCENDING = ASC = datastructures.Sentinel('ASCENDING')
DESCENDING = DSC = datastructures.Sentinel('DESCENDING')

# Query operators
EQUALS = EQ = datastructures.Sentinel('EQUALS')
NOT_EQUALS = NE = datastructures.Sentinel('NOT_EQUALS')
LESS_THAN = LT = datastructures.Sentinel('LESS_THAN')
LESS_THAN_EQUAL_TO = LE = datastructures.Sentinel('LESS_THAN_EQUAL_TO')
GREATER_THAN = GT = datastructures.Sentinel('GREATER_THAN')
GREATER_THAN_EQUAL_TO = GE = datastructures.Sentinel('GREATER_THAN_EQUAL_TO')
CONTAINS = IN = datastructures.Sentinel('CONTAINS')

# Logic operators
AND = datastructures.Sentinel('AND')
OR = datastructures.Sentinel('OR')

# Operator Constants
_operator_map = {
  EQUALS: operator.eq,
  NOT_EQUALS: operator.ne,
  LESS_THAN: operator.lt,
  LESS_THAN_EQUAL_TO: operator.le,
  GREATER_THAN: operator.gt,
  GREATER_THAN_EQUAL_TO: operator.ge,
  CONTAINS: operator.contains,
  AND: operator.__and__,
  OR: operator.__or__
}

_operator_strings = {
  EQUALS: '==',
  NOT_EQUALS: '!=',
  LESS_THAN: '<',
  LESS_THAN_EQUAL_TO: '<=',
  GREATER_THAN: '>',
  GREATER_THAN_EQUAL_TO: '>=',
  CONTAINS: 'CONTAINS',
  AND: 'AND',
  OR: 'OR'
}


class QueryOptions(object):

  ''' Holds a re-usable set of options for a :py:class:`Query`. '''

  # == Options == #
  options = frozenset((
    '_keys_only',
    '_ancestor',
    '_limit',
    '_offset',
    '_projection',
    '_hint',
    '_plan',
    '_cursor'
  ))

  __slots__ = frozenset(('__explicit__',)) | options

  option_names = frozenset(('_'.join(opt.split('_')[1:]) for opt in options))

  # == Option Defaults == #
  _defaults = {
    '_keys_only': False,
    '_ancestor': None,
    '_limit': -1,
    '_offset': 0,
    '_projection': None,
    '_hint': None,
    '_plan': None,
    '_cursor': None
  }

  ## == Internal Methods == ##
  def __init__(self, **kwargs):

    ''' Initialize this :py:class:`QueryOptions`. Map ``kwargs`` into local data
        properties that are abstracted behind getters/setters at the class
        level.

        :param **kwargs: Keyword argument options. Valid keys are listed in
          :py:attr:`__slots__`.

        :raises AttributeError: In the case that an invalid config key is found
          in ``kwargs``. Passed-up from :py:meth:`_set_option`.

        :returns: Nothing, as this is a constructor. '''

    self.__explicit__ = False  # initialize explicit flag
    map(lambda bundle: self._set_option(*bundle),
        map(lambda slot: (
          slot, kwargs.get(slot, datastructures._EMPTY)), self.option_names))

  def __iter__(self):

    ''' Iterate over options specified in this :py:class:`QueryOptions` object.
        Imitates the ``dict.iteritems`` interface, in that it yields
        ``(k, v)`` pairs. '''

    for option in self.option_names:
      yield option, self._get_option(option)

  def __enter__(self):

    ''' Enter an iteration mode whereby default *values* are omitted in favor of
        a sentinel that indicates empty fields.

        :returns: ``self``, in case an ``as`` block is used. '''

    self.__explicit__ = True
    return self

  def __exit__(self, type, value, traceback):

    ''' Exit the special iteration mode whereby default values are omitted.

        :returns: ``True`` in the case of a successful (read, non-excepting)
          enclosed block, else ``False`` to propagate the exception. '''

    self.__explicit__ = False
    if traceback: return False
    return True

  def __repr__(self):

    ''' Generate a pleasant string representation of this
        :py:class:`QueryOptions` object.

        :returns: Pleasant ``str`` label for this object. '''

    properties = []
    with self:
      for k, v in self:
        if v is not datastructures._EMPTY:
          properties.append((k, v))

    return "QueryOptions(%s)" % (
      ", ".join(map(lambda (k, v): "=".join((k, str(v))), properties))
    )

  ## == Protected Methods == ##
  def _set_option(self, name, value=datastructures._EMPTY):

    ''' Set the value of an option local to this :py:class:`QueryOptions`
        object. Calling without a ``value`` (which defaults to ``None``) resets
        the target key's value.

        :param name: Name (``str``) of the internal property we're setting.
        :param value: Value to set the property to. Defaults to ``None``.

        :raises ValueError: If ``name`` is not a ``basestring`` descendent.

        :raises AttributeError: If ``name`` is not a valid internal property
          name.

        :returns: ``self``, for chainability. '''

    if not isinstance(name, basestring):
      raise ValueError('Argument `name` of `_set_option` must'
                       ' be a string internal propery name.'
                       ' Got: "%s".' % str(name))  # pragma: no cover

    name = '_' + name if name[0] != '_' else name  # build internal name

    if name not in self.__slots__:
      raise AttributeError('`QueryOptions` object has no option by'
                           ' the name "%s".' % name)

    setattr(self, name, value)  # set value and return
    return self

  def _get_option(self, name, default=datastructures._EMPTY):

    ''' Get the value of an option local to this :py:class:`QueryOptions`
        object.

        :param name: Name (``str``) of the internal property we're getting.

        :param default: Default value to return if no value was found at
          ``name``. Defaults to ``None``.

        :raises ValueError: If ``name`` is not a ``basestring`` descendent.

        :raises AttributeError: If ``name`` is not a valid internal property
          name.

        :returns: Configuration value at ``name``, or ``default`` if no value
          was found. '''

    if not isinstance(name, basestring):  # pragma: no cover
      raise ValueError('Argument `name` of `_get_option` must'
                       ' be a string internal property name.'
                       ' Got: "%s".' % str(name))

    name = '_' + name  # build internal name

    if name not in self.__slots__:
      raise AttributeError('`QueryOptions` object has no option by'
                           ' the name "%s".' % name)  # pragma: no cover

    val = getattr(self, name)  # get value

    # return default value if empty slot was found, otherwise return value
    if val is datastructures._EMPTY:
      if self.__explicit__:
        return datastructures._EMPTY
      if default is datastructures._EMPTY:
        return self._defaults.get(name, None)
      return default  # pragma: no cover
    return val

  def overlay(self, other, override=False):

    ''' Combine this :py:class:`QueryOptions` object with another one, by
        merging the ``other`` object's settings into this one.

        :param other: Other :py:class:`QueryOptions` object to collect overriden
          property values from.

        :param override:

        :returns: Resulting merged object, which is simply ``self``. '''

    with other:
      with self:
        for option, value in other:
          if value is not datastructures._EMPTY:
            this_value = self._get_option(option)
            if (this_value is datastructures._EMPTY) or override:
              self._set_option(option, value)
    return self


  ## == Public Properties == ##

  # ``keys_only`` flag - return keys instead of entities
  keys_only = property(lambda self: self._get_option('keys_only'))

  # ``ancestor`` filter - restrict results by key ancestry
  ancestor = property(lambda self: self._get_option('ancestor'))

  # ``limit`` - return a limited number of query results
  limit = property(lambda self: self._get_option('limit'))

  # ``offset`` - skip an amount of records before building results
  offset = property(lambda self: self._get_option('offset'))

  # ``projection`` - retrieve entity values from indexes while fulfilling query
  projection = property(lambda self: self._get_option('projection'))

  # ``plan`` - cached plan to fulfill the query (optional)
  plan = property(lambda self: self._get_option('plan'),
                  lambda self, value: self._set_option('plan', value))

  # ``cursor`` - result cursor, for paging or long queries (optional)
  cursor = property(lambda self: self._get_option('cursor'),
                    lambda self, value: self._set_option('cursor', value))


class GraphQueryOptions(QueryOptions):

  ''' Specifies Graph-related query options in addition to standard ``Query``
      properties. '''

  # == Options == #
  options = QueryOptions.options | frozenset((
    '_base',
  ))

  __slots__ = QueryOptions.options | options

  option_names = frozenset(('_'.join(opt.split('_')[1:]) for opt in options))

  # == Option Defaults == #
  _defaults = dict(QueryOptions._defaults, **{
    '_graph_base': None
  })


  ## == Public Properties == ##

  # ``base`` - graph-specific base key
  base = property(lambda self: self._get_option('base'))


class AbstractQuery(object):

  ''' Specifies base structure and interface for all query classes. '''

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def filter(self, expression):

    ''' Add a filter to the active :py:class:`Query` at ``self``.

        :param expression: Filter expression to apply during query planning.
        :raises NotImplementedError: Always, as this method is abstract.
        :returns: ``self``, for chainability. '''

    raise NotImplementedError('`filter` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover

  @abc.abstractmethod
  def sort(self, expression):

    ''' Add a sort directive to the active :py:class:`Query` at ``self``.

        :param expression: Sort expression to apply to the target result set.
        :raises NotImplementedError: Always, as this method is abstract.
        :returns: ``self``, for chainability. '''

    raise NotImplementedError('`sort` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover

  @abc.abstractmethod
  def hint(self, directive):

    ''' Pass a hint to the query-planning subsystem for how this query could
        most efficiently be satisfied.

        :param expression: Hint expression to take into consideration.
        :raises NotImplementedError: Always, as this method is abstract.
        :returns: ``self``, for chainability. '''

    raise NotImplementedError('`hint` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover

  @abc.abstractmethod
  def fetch(self, **options):

    ''' Fetch results for a :py:class:`Query`, via the underlying driver's
        :py:meth:`execute_query` method.

        :param **options: Query options to build into a :py:class:`QueryOptions`
          object.

        :raises NotImplementedError: Always, as this method is abstract.

        :returns: Iterable (``list``) of matching :py:class:`model.Model`
          entities (or :py:class:`model.Key` objects if ``keys_only`` is
          truthy) yielded from current :py:class:`Query`, or an empty ``list``
          if no results were found. '''

    raise NotImplementedError('`fetch` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover

  @abc.abstractmethod
  def get(self, **options):

    ''' Get a single result (by default, the first) matching a
        :py:class:`Query`.

        :param **options: Query options to build into a
          :py:class:`QueryOptions` object.

        :raises NotImplementedError: Always, as this method is abstract.

        :returns: Single result :py:class:`model.Model` (or
          :py:class:`model.Key` if ``keys_only`` is truthy) matching the current
          :py:class:`Query`, or ``None`` if no matching entities were found. '''

    raise NotImplementedError('`fetch` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover


class Query(AbstractQuery):

  ''' Top-level class representing a specification for a query across data
      accessible to the canteen model layer, using an adapter that supports the
      :py:class:`IndexedModelAdapter` interface. '''

  kind = None  # model kind
  sorts = None  # sort directives
  options = None  # attached query options
  filters = None  # filter directives

  def __init__(self, kind=None, filters=None, sorts=None, **kwargs):

    ''' Initialize this :py:class:`Query`, assigning any properties/config
        passed in via ``kwargs`` and such.

        :param kind: Model kind that we wish to query upon, or ``None`` to
          specify a *kindless* query (meaning that it matches *all* available
          model kinds, if implemented).

        :param filters: Array of ``Filter`` objects to add to the newly-prepared
          ``Query`` object. ``Filter``s can also be added via ``Query.filter``.

        :param sorts: Array of ``Sort`` objects to add to the newly-prepared
          ``Query`` object. ``Sort``s can also be added via ``Query.sort``.

        :param **kwargs: Additional options to pass to ``QueryOptions``. If an
          item exists at ``kwargs['options']``, it is used *in place* of
          generated query options. '''

    filters = filters and ([filters] if not (
      isinstance(filters, (list, tuple))) else filters) or None

    sorts = sorts and ([sorts] if not (
      isinstance(sorts, (list, tuple))) else sorts) or None

    options = kwargs.get('options', QueryOptions(**kwargs))
    self.kind, self.filters, self.sorts, self.options = (
      kind, filters or [], sorts or [], options)

  def __repr__(self):

    ''' Generate a string representation of this :py:class:`Query`.

        :returns: String representation of the current :py:class:`Query`. '''

    return "Query(%s, filter=%s, sort=%s, options=%s)" % (
      self.kind.kind(),
      '[' + ','.join((str(f) for f in self.filters)) + ']',
      '[' + ','.join((str(s) for s in self.sorts)) + ']',
      self.options.__repr__()
    )

  # @TODO(sgammon): async methods to execute
  def _execute(self, options=None, **kwargs):

    ''' Internal method to execute a query, optionally along with some override
        options.

        .. note: This method will eventually accompany an async equivalent,
             which this will make use of runtime async tools under-the-hood.

        :param options:

        :param **kwargs: Keyword arguments of query config (i.e. valid and
          registered on :py:class:`QueryOptions`) to pass to the options object
          built to execute the query.

        :raises AttributeError: In the case that an invalid/unknown query
          configuration key is encountered. Passed up from
          :py:class:`QueryOptions`.

        :raises NotImplementedError: In the case that a ``kindless`` or
          ``projection`` query is encountered, as those features are not yet
          supported.

        :returns: Synchronously-retrieved results to this :py:class:`Query`. '''

    ## build query options
    if self.options and options:
      options = self.options.overlay(options)
    else:
      options = (options or (
        kwargs.get('options', (
          QueryOptions(**kwargs) if kwargs else self.options))))

    ## fail for projection queries
    if options.projection:
      raise NotImplementedError('Projection queries are not'
                                ' yet supported.')  # pragma: no cover

    if self.kind:  # kinded query

      # delegate to driver
      return self.kind.__adapter__._execute_query(self)

    else:

      # kindless queries are not yet supported
      raise NotImplementedError('Kindless queries are not'
                                ' yet supported.')  # pragma: no cover

  def filter(self, expression):

    ''' Add a filter to this :py:class:`Query`.

        :param expression: Expression descriptor of type :py:class:`Filter`.

        :raises:
        :returns: '''

    if isinstance(expression, Filter):
      self.filters.append(expression)
    else:  # pragma: no cover
      raise NotImplementedError('Query method `filter` does not yet support'
                                ' non-`Filter` component types.')
    return self

  def sort(self, expression):

    ''' Add a sort order to this :py:class:`Query`.

        :param expression: Expression descriptor of type :py:class:`Sort`.

        :raises:
        :returns: '''

    from canteen import model

    if isinstance(expression, model.Property):  # pragma: no cover
      # default to descending sort
      self.sorts.append(-expression)
    if isinstance(expression, Sort):
      self.sorts.append(expression)
    else:  # pragma: no cover
      raise NotImplementedError('Query method `sort` does not yet support non-'
                                '`Sort` component types.')
    return self

  def hint(self, directive):  # pragma: no cover

    ''' Provide an external hint to the query planning logic about how to plan
        the query.

        Currently stubbed.

        :param directive:

        :raises NotImplementedError: Always,
        as this method is currently stubbed.

        :returns: ``self``, for chainability. '''

    # @TODO(sgammon): fill out query hinting logic
    raise NotImplementedError('Query method `hint` is currently stubbed.')

  def get(self, **options):

    ''' Get a single result (by default, the first) matching a
        :py:class:`Query`.

        :param **options: Accepts any valid and registered options on
          :py:class:`QueryOptions`.

        :returns: Single result :py:class:`model.Model` (or
          :py:class:`model.Key` if ``keys_only`` is truthy) matching the current
          :py:class:`Query`, or ``None`` if no matching entities were found. '''

    result = self._execute(options=QueryOptions(**options))
    return result[0] if result else result

  def fetch(self, **options):

    ''' Fetch results for the currently-built :py:class:`Query`, executing it
        across the attached ``kind``'s attached model adapter.

        :param **options: Accepts any valid and registered options on
          :py:class:`QueryOptions`.

        :returns: Iterable (``list``) of matching model entities. '''

    return self._execute(options=QueryOptions(**options) if options else None)

  def fetch_page(self, **options):

    ''' Fetch a page of results, potentially as the next in a sequence of page
        requests.

        :param **options: Accepts any valid and registered options on
          :py:class:`QueryOptions`.

        :raises:

        :returns: '''

    # @TODO(sgammon): build out paging support
    raise NotImplementedError('Query method `fetch_page`'
                              ' is currently stubbed.')  # pragma: no cover


class QueryComponent(object):

  ''' Top-level abstract class for a component of a :py:class:`Query`, which is
      usually an attached specification like a :py:class:`Filter` or
      :py:class:`Sort`. '''

  __metaclass__ = abc.ABCMeta

  ## == Component State == ##
  kind = None  # kind of property
  target = None  # property to operate on
  operator = None  # operator selection

  ## == Constants == ##
  PROPERTY = PROPERTY
  KEY_KIND = KEY_KIND
  KEY_ANCESTOR = KEY_ANCESTOR


class Filter(QueryComponent):

  ''' Query component specification parent for a generic filter, used to
      traverse indexes and find entities to return that match. '''

  ## == Filter State == ##
  value = None  # value to match
  chain = None  # chained AND and OR filters
  sub_operator = None  # subquery operator, if any (makes this a subfilter)

  ## == Operators == ##
  EQUALS = EQ = EQUALS
  NOT_EQUALS = NEQ = NOT_EQUALS
  LESS_THAN = LT = LESS_THAN
  LESS_THAN_EQUAL_TO = LE = LESS_THAN_EQUAL_TO
  GREATER_THAN = GT = GREATER_THAN
  GREATER_THAN_EQUAL_TO = GE = GREATER_THAN_EQUAL_TO
  CONTAINS = IN = CONTAINS

  def __init__(self, prop, value,
                            AND=None,
                            OR=None,
                            type=PROPERTY,
                            operator=EQUALS):

    ''' Initialize this :py:class:`Filter`.

        :param prop:
        :param value:
        :param AND:
        :param OR:
        :param type:
        :param operator:

        :raises:

        :returns: '''

    from canteen import model
    value = model.AbstractModel._PropertyValue(value, False)  # make a value

    # repeated properties do not support EQUALS -> only CONTAINS
    if prop._repeated and operator is EQUALS:
      self.operator = operator = CONTAINS

    self.target, self.value, self.kind, self.operator, self.chain = (
      prop, value, type, operator, [])

    if AND or OR:
      for var in (AND, OR):
        self.chain += (var if (
          isinstance(var, (list, tuple, set, frozenset))) else [var])

  def __repr__(self):

    ''' Generate a string representation of this :py:class:`Filter`.

        :returns: '''

    return 'Filter(%s %s %s)' % (
      (self.sub_operator.name + ' ') if self.sub_operator else (
        '' + self.target.name),
      _operator_strings[self.operator], str(self.value))

  def AND(self, filter_expression):

    ''' Chain a query with this one, logically separated by an ``AND`` operator.

        :param filter_expression: Other filter to add to this filter's chain.

        :returns: ``self``, for the ability to further chain this query.'''

    self.chain += [filter_expression.set_subquery_operator(AND)]
    return self

  def OR(self, filter_expression):

    ''' Chain a query with this one, logically separated by an ``OR`` operator.

        :param filter_expression: Other filter to add to this filter's chain.

        :returns: ``self``, for the ability to further chain this query.'''

    self.chain += [filter_expression.set_subquery_operator(OR)]
    return self

  def set_subquery_operator(self, operator):

    ''' Internal function for setting a query object's subquery operator, which
        is required to support ``AND/OR`` filter chaining.

        :param operator: Set the local query's subquery operator to this value.

        :returns: ``self``, for the ability to further chain this query. '''

    self.sub_operator = operator
    return self

  def match(self, target):

    ''' Match this query's target, operator, and embedded data against a target
        entity or value.

        :param target: May be a full ``Model``  object or raw value. Matched
          against this handler's constraints.

        :raises:

        :returns: ``True`` if the target ``Model`` or value matches this
          filter's contraints, ``False`` otherwise. '''

    if self.operator not in _operator_map:  # pragma: no cover
      raise RuntimeError('Invalid comparison operator'
                         ' could not be matched: "%s".' % self.operator)

    try:
      # it's a raw entity -> dict
      if isinstance(target, dict):
        if self.target.name in target:
          return _operator_map[self.operator](*(
            target[self.target.name], self.value.data))
        # no such property
        return False  # pragma: no cover

      # it's a raw value of some sort
      if isinstance(target, self.target._basetype):
        return _operator_map[self.operator](target, self.value.data)

      # it's a model or something
      return _operator_map[self.operator](*(
        getattr(target, self.target.name), self.value.data))

    except AttributeError:  # pragma: no cover
      return False  # no such property

  def __call__(self, target):

    ''' Proxy to ``self.match``, which matches a target ``Model`` or value
        against this filter's constraints.

        :param target: Target ``model.Model`` instance or raw value to match
          against.

        :returns: ``True`` if ``target`` matches, otherwise ``False``. '''

    return self.match(target)  # pragma: no cover


class KeyFilter(Filter):

  ''' Expresses a filter that applies to an entity's associated
      :py:class:`model.Key`, or one of the member components thereof. '''

  # == Constants == #
  KIND = KEY_KIND
  ANCESTOR = KEY_ANCESTOR


class Sort(QueryComponent):

  ''' Expresses a directive to sort resulting entities by a property in a given
      direction. '''

  ## == Sort Orders == ##
  ASC = ASCENDING = ASC
  DSC = DESCENDING = DSC

  def __init__(self, prop, type=PROPERTY, operator=ASC):

    ''' Initialize this :py:class:`Sort`.

        :param prop: Subject property to sort upon.

        :param type: Type of sort to apply, defaults to a ``PROPERTY``-based
          sort, which sorts upon property values.

        :param operator: Either ascending (``ASC`` or ``ASCENDING`` global
          symbols) or descending (``DSC`` or ``DESCENDING`` global symbols). '''

    self.target, self.kind, self.operator = prop, type, operator

  def __repr__(self):

    ''' Generate a string representation of this :py:class:`Sort`.

        :returns: Pleasant string representation of this ``Sort``, formatted
          like ``Sort(target, operator)``. '''

    return 'Sort(%s, %s)' % (self.target.name, self.operator)
