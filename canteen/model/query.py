# -*- coding: utf-8 -*-

"""

  model queries
  ~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

"""


__version__ = 'v5'


# stdlib
import abc
import base64
import operator

# datastructures
from canteen.util.struct import (EMPTY,
                                 Sentinel)


## Globals / Constants

# Filter components
_TARGET_KEY = Sentinel('KEY')
PROPERTY = Sentinel('PROPERTY')
KEY_KIND = Sentinel('KEY_KIND')
KEY_ANCESTOR = Sentinel('KEY_ANCESTOR')
EDGES = Sentinel('EDGES')
NEIGHBORS = Sentinel('NEIGHBORS')

# Sort directions
ASCENDING = ASC = Sentinel('ASCENDING')
DESCENDING = DSC = Sentinel('DESCENDING')

# Query operators
EQUALS = EQ = Sentinel('EQUALS')
NOT_EQUALS = NE = Sentinel('NOT_EQUALS')
LESS_THAN = LT = Sentinel('LESS_THAN')
LESS_THAN_EQUAL_TO = LE = Sentinel('LESS_THAN_EQUAL_TO')
GREATER_THAN = GT = Sentinel('GREATER_THAN')
GREATER_THAN_EQUAL_TO = GE = Sentinel('GREATER_THAN_EQUAL_TO')
CONTAINS = IN = Sentinel('CONTAINS')

# Logic operators
AND = Sentinel('AND')
OR = Sentinel('OR')

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
  OR: operator.__or__}

_operator_strings = {
  EQUALS: '==',
  NOT_EQUALS: '!=',
  LESS_THAN: '<',
  LESS_THAN_EQUAL_TO: '<=',
  GREATER_THAN: '>',
  GREATER_THAN_EQUAL_TO: '>=',
  CONTAINS: 'CONTAINS',
  AND: 'AND',
  OR: 'OR'}


class QueryOptions(object):

  """ Holds a re-usable set of options for a :py:class:`Query`. """

  magic_symbol = 0x0

  # == Options == #
  options = frozenset((
    '_keys_only',
    '_ancestor',
    '_limit',
    '_offset',
    '_projection',
    '_hint',
    '_plan',
    '_cursor'))

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
    '_cursor': None}

  ## == Internal Methods == ##
  def __init__(self, **kwargs):

    """ Initialize this :py:class:`QueryOptions`. Map ``kwargs`` into local data
        properties that are abstracted behind getters/setters at the class
        level.

        :param **kwargs: Keyword argument options. Valid keys are listed in
          :py:attr:`__slots__`.

        :raises AttributeError: In the case that an invalid config key is found
          in ``kwargs``. Passed-up from :py:meth:`_set_option`.

        :returns: Nothing, as this is a constructor. """

    self.__explicit__ = False  # initialize explicit flag
    map(lambda bundle: self._set_option(*bundle),
        map(lambda slot: (slot, kwargs.get(slot, EMPTY)), self.option_names))

  def __iter__(self):

    """ Iterate over options specified in this :py:class:`QueryOptions` object.
        Imitates the ``dict.iteritems`` interface, in that it yields
        ``(k, v)`` pairs. """

    for option in self.option_names:
      yield option, self._get_option(option)

  def __enter__(self):

    """ Enter an iteration mode whereby default *values* are omitted in favor of
        a sentinel that indicates empty fields.

        :returns: ``self``, in case an ``as`` block is used. """

    self.__explicit__ = True
    return self

  def __exit__(self, type, value, traceback):

    """ Exit the special iteration mode whereby default values are omitted.

        :returns: ``True`` in the case of a successful (read, non-excepting)
          enclosed block, else ``False`` to propagate the exception. """

    self.__explicit__ = False
    if traceback: return False
    return True

  def __repr__(self):

    """ Generate a pleasant string representation of this
        :py:class:`QueryOptions` object.

        :returns: Pleasant ``str`` label for this object. """

    properties = []
    with self:
      for k, v in self:
        if v is not EMPTY:
          properties.append((k, v))

    return "QueryOptions(%s)" % (
      ", ".join(map(lambda (k, v): "=".join((k, str(v))), properties)))

  ## == Protected Methods == ##
  def _set_option(self, name, value=EMPTY, _setter=False):

    """ Set the value of an option local to this :py:class:`QueryOptions`
        object. Calling without a ``value`` (which defaults to ``None``) resets
        the target key's value.

        :param name: Name (``str``) of the internal property we're setting.
        :param value: Value to set the property to. Defaults to ``None``.
        :param _setter: Internal ``bool``-type param indicating we're accessing
          this from a setter, so we should not return a value.

        :raises ValueError: If ``name`` is not a ``basestring`` descendent.

        :raises AttributeError: If ``name`` is not a valid internal property
          name.

        :returns: ``self``, for chainability. """

    if not isinstance(name, basestring):
      raise ValueError('Argument `name` of `_set_option` must'
                       ' be a string internal propery name.'
                       ' Got: "%s".' % str(name))  # pragma: no cover

    # build internal name
    name = '_' + unicode(name) if name[0] != '_' else unicode(name)

    if name not in self.__slots__:
      raise AttributeError('`QueryOptions` object has no option by'
                           ' the name "%s".' % name)

    setattr(self, name, value)  # set value and return
    if not _setter:
      return self

  def _get_option(self, name, default=EMPTY):

    """ Get the value of an option local to this :py:class:`QueryOptions`
        object.

        :param name: Name (``str``) of the internal property we're getting.

        :param default: Default value to return if no value was found at
          ``name``. Defaults to ``None``.

        :raises ValueError: If ``name`` is not a ``basestring`` descendent.

        :raises AttributeError: If ``name`` is not a valid internal property
          name.

        :returns: Configuration value at ``name``, or ``default`` if no value
          was found. """

    if not isinstance(name, basestring):  # pragma: no cover
      raise ValueError('Argument `name` of `_get_option` must'
                       ' be a string internal property name.'
                       ' Got: "%s".' % name)

    name = '_%s' % name  # build internal name

    if name not in self.__slots__:
      raise AttributeError('`QueryOptions` object has no option by'
                           ' the name "%s".' % name)  # pragma: no cover

    val = getattr(self, name)  # get value

    # return default value if empty slot was found, otherwise return value
    if val is EMPTY:
      if self.__explicit__:
        return EMPTY
      if default is EMPTY:
        return self._defaults.get(name, None)
      return default  # pragma: no cover
    return val

  def overlay(self, other, override=False):

    """ Combine this :py:class:`QueryOptions` object with another one, by
        merging the ``other`` object's settings into this one.

        :param other: Other :py:class:`QueryOptions` object to collect overriden
          property values from.

        :param override:

        :returns: Resulting merged object, which is simply ``self``. """

    with other:
      with self:
        for option, value in other:
          if value is not EMPTY:
            this_value = self._get_option(option)
            if (this_value is EMPTY) or override:
              self._set_option(option, value)
    return self

  def pack(self, encode=True):

    """ Pack this set of ``QueryOptions`` into a string describing the
        constituent settings it contains.

        :param encode: Obfuscate/encode in ``base64`` before returning.

        :return: ``unicode`` string that can be translated back into a full
         ``QueryOptions`` instance and represents (uniquely) that set of
         query option values. """

    from canteen import model

    items = [self.magic_symbol]
    for key in sorted(self.options):
      value = getattr(self, key[1:], self._defaults[key])

      if isinstance(value, bool): items.append(int(value))
      elif isinstance(value, model.Key): items.append(value.urlsafe())
      elif isinstance(value, (int, long, float)): items.append(value)
      elif value is None: items.append('')
      else: items.append(value)  # pragma: no cover
    items = tuple(items)

    return (
      base64.b64encode(":".join(map(unicode, items))) if encode else items)

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
                  lambda self, v: self._set_option('plan', v, _setter=True))

  # ``cursor`` - result cursor, for paging or long queries (optional)
  cursor = property(lambda self: self._get_option('cursor'),
                    lambda self, v: self._set_option('cursor', v, _setter=True))


class AbstractQuery(object):

  """ Specifies base structure and interface for all query classes. """

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def filter(self, expression):  # pragma: no cover

    """ Add a filter to the active :py:class:`Query` at ``self``.

        :param expression: Filter expression to apply during query planning.
        :raises NotImplementedError: Always, as this method is abstract.
        :returns: ``self``, for chainability. """

    raise NotImplementedError('`filter` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover

  @abc.abstractmethod
  def sort(self, expression):  # pragma: no cover

    """ Add a sort directive to the active :py:class:`Query` at ``self``.

        :param expression: Sort expression to apply to the target result set.
        :raises NotImplementedError: Always, as this method is abstract.
        :returns: ``self``, for chainability. """

    raise NotImplementedError('`sort` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover

  @abc.abstractmethod
  def hint(self, directive):  # pragma: no cover

    """ Pass a hint to the query-planning subsystem for how this query could
        most efficiently be satisfied.

        :param expression: Hint expression to take into consideration.
        :raises NotImplementedError: Always, as this method is abstract.
        :returns: ``self``, for chainability. """

    raise NotImplementedError('`hint` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover

  @abc.abstractmethod
  def fetch(self, **options):  # pragma: no cover

    """ Fetch results for a :py:class:`Query`, via the underlying driver's
        :py:meth:`execute_query` method.

        :param **options: Query options to build into a :py:class:`QueryOptions`
          object.

        :raises NotImplementedError: Always, as this method is abstract.

        :returns: Iterable (``list``) of matching :py:class:`model.Model`
          entities (or :py:class:`model.Key` objects if ``keys_only`` is
          truthy) yielded from current :py:class:`Query`, or an empty ``list``
          if no results were found. """

    raise NotImplementedError('`fetch` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover

  @abc.abstractmethod
  def get(self, **options):  # pragma: no cover

    """ Get a single result (by default, the first) matching a
        :py:class:`Query`.

        :param **options: Query options to build into a
          :py:class:`QueryOptions` object.

        :raises NotImplementedError: Always, as this method is abstract.

        :returns: Single result :py:class:`model.Model` (or
          :py:class:`model.Key` if ``keys_only`` is truthy) matching the current
          :py:class:`Query`, or ``None`` if no matching entities were found. """

    raise NotImplementedError('`fetch` is abstract and may not'
                              ' be invoked directly.')  # pragma: no cover


class GraphQueryOptions(QueryOptions):

  """ Specifies Graph-related query options in addition to standard ``Query``
      properties. """

  magic_symbol = 0x1

  # == Options == #
  options = QueryOptions.options | frozenset((
    '_base',))

  __slots__ = QueryOptions.options | options

  option_names = frozenset(('_'.join(opt.split('_')[1:]) for opt in options))

  # == Option Defaults == #
  _defaults = dict(QueryOptions._defaults, **{
    '_graph_base': None})


  # # == Public Properties == ##

  # ``base`` - graph-specific base key
  base = property(lambda self: self._get_option('base'))


class Query(AbstractQuery):

  """ Top-level class representing a specification for a query across data
      accessible to the canteen model layer, using an adapter that supports the
      :py:class:`IndexedModelAdapter` interface. """

  kind = None  # model kind
  sorts = None  # sort directives
  options = None  # attached query options
  adapter = None  # attached adapter, if any
  filters = None  # filter directives

  def __init__(self, kind=None, filters=None, sorts=None, **kwargs):

    """ Initialize this :py:class:`Query`, assigning any properties/config
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
          generated query options. """

    filters = filters and ([filters] if not (
      isinstance(filters, (list, tuple))) else filters) or None

    sorts = sorts and ([sorts] if not (
      isinstance(sorts, (list, tuple))) else sorts) or None

    # preload adapter for fetch/get
    if 'adapter' in kwargs:
      self.adapter = kwargs['adapter']
      del kwargs['adapter']

    options = kwargs.get('options', QueryOptions(**kwargs))
    self.kind, self.filters, self.sorts, self.options = (
      kind, filters or [], sorts or [], options)

  def __repr__(self):

    """ Generate a string representation of this :py:class:`Query`.

        :returns: String representation of the current :py:class:`Query`. """

    return "Query(%s, filter=%s, sort=%s, options=%s)" % (
      self.kind.kind(),
      '[' + ','.join((str(f) for f in self.filters)) + ']',
      '[' + ','.join((str(s) for s in self.sorts)) + ']',
      self.options.__repr__())

  # @TODO(sgammon): async methods to execute
  def _execute(self, options=None, adapter=None, **kwargs):

    """ Internal method to execute a query, optionally along with some override
        options.

        .. note: This method will eventually accompany an async equivalent,
             which this will make use of runtime async tools under-the-hood.

        :param options:
        :param adapter:

        :param **kwargs: Keyword arguments of query config (i.e. valid and
          registered on :py:class:`QueryOptions`) to pass to the options object
          built to execute the query.

        :raises AttributeError: In the case that an invalid/unknown query
          configuration key is encountered. Passed up from
          :py:class:`QueryOptions`.

        :raises NotImplementedError: In the case that a ``kindless`` or
          ``projection`` query is encountered, as those features are not yet
          supported.

        :returns: Synchronously-retrieved results to this :py:class:`Query`. """

    from canteen import model

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

    if adapter: return adapter._execute_query(self)
    if self.adapter: return self.adapter._execute_query(self)
    if self.kind: return self.kind.__adapter__._execute_query(self)
    return model.Model.__adapter__._execute_query(self)

  def filter(self, expression):

    """ Add a filter to this :py:class:`Query`.

        :param expression: Expression descriptor of type :py:class:`Filter`.

        :raises:
        :returns: """

    if isinstance(expression, Filter):
      self.filters.append(expression)
    else:  # pragma: no cover
      raise NotImplementedError('Query method `filter` does not yet support'
                                ' non-`Filter` component types.')
    return self

  def sort(self, expression):

    """ Add a sort order to this :py:class:`Query`.

        :param expression: Expression descriptor of type :py:class:`Sort`.

        :raises:
        :returns: """

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

    """ Provide an external hint to the query planning logic about how to plan
        the query.

        Currently stubbed.

        :param directive:

        :raises NotImplementedError: Always,
        as this method is currently stubbed.

        :returns: ``self``, for chainability. """

    # @TODO(sgammon): fill out query hinting logic
    raise NotImplementedError('Query method `hint` is currently stubbed.')

  def get(self, adapter=None, **options):

    """ Get a single result (by default, the first) matching a
        :py:class:`Query`.

        :param **options: Accepts any valid and registered options on
          :py:class:`QueryOptions`.

        :param adapter: Adapter to use for the ``get`` operation.

        :returns: Single result :py:class:`model.Model` (or
          :py:class:`model.Key` if ``keys_only`` is truthy) matching the current
          :py:class:`Query`, or ``None`` if no matching entities were found. """

    options['limit'] = 1  # always has a limit of 1
    result = self._execute(QueryOptions(**options), adapter)
    return result[0] if result else None

  def fetch(self, adapter=None, **options):

    """ Fetch results for the currently-built :py:class:`Query`, executing it
        across the attached ``kind``'s attached model adapter.

        :param **options: Accepts any valid and registered options on
          :py:class:`QueryOptions`.

        :returns: Iterable (``list``) of matching model entities. """

    return self._execute(
      options=QueryOptions(**options) if options else None,
      adapter=adapter)

  def fetch_page(self, **options):

    """ Fetch a page of results, potentially as the next in a sequence of page
        requests.

        :param **options: Accepts any valid and registered options on
          :py:class:`QueryOptions`.

        :raises:

        :returns: """

    # @TODO(sgammon): build out paging support
    raise NotImplementedError('Query method `fetch_page`'
                              ' is currently stubbed.')  # pragma: no cover

  def pack(self, encode=True):

    """ Pack this ``Query`` instance into a structure uniquely describing it,
        with the ability to optionally expand that into a ``Query`` object
        representing the same operations.

        :param encode: ``bool`` flag, indicates whether to encode the packed
          output in ``base64`` by default. Defaults to ``True``, which *does*
          encode on the way out.

        :return: ``tuple`` instance describing the structure of this query if
          ``encode`` is ``False``, otherwise a ``unicode`` string (encoded in
          ``base64``) describing this query's structure. """

    bundles = []
    for group in ((self.options,), self.filters, self.sorts):
      for constituent in group:
        if encode:
          bundles.append(':'.join(map(unicode, constituent.pack(False))))
        else:
          bundles.append(constituent.pack(False))
    bundles = tuple(bundles)

    return base64.b64encode(",".join(bundles)) if encode else bundles


class QueryComponent(object):

  """ Top-level abstract class for a component of a :py:class:`Query`, which is
      usually an attached specification like a :py:class:`Filter` or
      :py:class:`Sort`. """

  __metaclass__ = abc.ABCMeta

  ## == Component State == ##
  kind = None  # kind of property
  target = None  # property to operate on
  operator = None  # operator selection

  ## == Constants == ##
  PROPERTY = PROPERTY
  KEY_KIND = KEY_KIND
  KEY_ANCESTOR = KEY_ANCESTOR

  def pack(self, encode=True):

    """ Pack a ``QueryComponent`` object into a structure uniquely describing
        the operation it specifies, that can optionally later be used to
        reproduce another ``QueryComponent`` object just like it.

        :param encode: ``bool`` flag indicating whether to encode the structure
          as ``base64`` before returning.

        :return: ``tuple`` structure descrbing this ``QueryComponent`` (if
          ``encode`` is ``False``), otherwise ``unicode`` instance of
          ``base64``-encoded string. """

    from canteen import model

    items = [self.magic_symbol]
    for item in self.items:
      value = getattr(self, item, None)

      if isinstance(value, model.Model._PropertyValue):
        value = value.data

      if value is None:
        items.append('')

      elif isinstance(value, model.Key):
        items.append(value.urlsafe())

      elif isinstance(value, model.Property):
        items.append(value.name)

      else:
        items.append(value)
    items = tuple(items)

    return items if not encode else base64.b64encode(
      ':'.join(map(unicode, items)))

class Filter(QueryComponent):

  """ Query component specification parent for a generic filter, used to
      traverse indexes and find entities to return that match. """

  magic_symbol = 0x2
  generic_name = 'Property'
  items = (
    'kind',
    'operator',
    'value')

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

    """ Initialize this :py:class:`Filter`.

        :param prop: Property object to filter against.

        :param value: Value to filter entity ``prop`` containers against.

        :param AND: Subfilters to chain with a logical ``AND``.

        :param OR: Subfilters to chain with a logical ``OR``.

        :param type: Type of filter to create, defaults to ``PROPERTY``,
          meaning it is a filter against a ``value`` in properties contained by
          stored entities.

        :param operator: Operator to use for comparing ``prop`` values against
          ``value``. Can be one of the following options:
          - ``EQUALS``, equating to ``x == y``
          - ``NOT_EQUALS``, equating to ``x != y``
          - ``LESS_THAN``, equating to ``x < y``
          - ``LESS_THAN_EQUAL_TO``, equating to ``x <= y``
          - ``GREATER_THAN``, equating to ``x > y``
          - ``GREATER_THAN_EQUAL_TO``, equating to ``x >= y``
          - ``CONTAINS``, equating to ``x in y`` """

    from canteen import model
    value = model.AbstractModel._PropertyValue(value)  # make a value

    # repeated properties do not support EQUALS -> only CONTAINS
    if prop and prop._repeated and operator is EQUALS:
      self.operator = operator = CONTAINS

    self.target, self.value, self.kind, self.operator, self.chain = (
      prop, value, type, operator, [])

    if AND or OR:
      for var in (AND, OR):
        self.chain += (var if (
          isinstance(var, (list, tuple, set, frozenset))) else [var])

  def __repr__(self):

    """ Generate a string representation of this :py:class:`Filter`.

        :returns: """

    return 'Filter(%s %s %s)' % (
      (self.sub_operator.name + ' ') if self.sub_operator else (
        '' + getattr(self.target, 'name', self.generic_name)),
      _operator_strings[self.operator], str(self.value))

  def AND(self, filter_expression):

    """ Chain a query with this one, logically separated by an ``AND`` operator.

        :param filter_expression: Other filter to add to this filter's chain.

        :returns: ``self``, for the ability to further chain this query."""

    self.chain += [filter_expression.set_subquery_operator(AND)]
    return self

  def OR(self, filter_expression):

    """ Chain a query with this one, logically separated by an ``OR`` operator.

        :param filter_expression: Other filter to add to this filter's chain.

        :returns: ``self``, for the ability to further chain this query."""

    self.chain += [filter_expression.set_subquery_operator(OR)]
    return self

  def set_subquery_operator(self, operator):

    """ Internal function for setting a query object's subquery operator, which
        is required to support ``AND/OR`` filter chaining.

        :param operator: Set the local query's subquery operator to this value.

        :returns: ``self``, for the ability to further chain this query. """

    self.sub_operator = operator
    return self

  def match(self, target):

    """ Match this query's target, operator, and embedded data against a target
        entity or value.

        :param target: May be a full ``Model``  object or raw value. Matched
          against this handler's constraints.

        :raises:

        :returns: ``True`` if the target ``Model`` or value matches this
          filter's contraints, ``False`` otherwise. """

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

    """ Proxy to ``self.match``, which matches a target ``Model`` or value
        against this filter's constraints.

        :param target: Target ``model.Model`` instance or raw value to match
          against.

        :returns: ``True`` if ``target`` matches, otherwise ``False``. """

    return self.match(target)  # pragma: no cover


class KeyFilter(Filter):

  """ Expresses a filter that applies to an entity's associated
      :py:class:`model.Key`, or one of the member components thereof. """

  magic_symbol = 0x3
  items = (
    'kind',
    'operator',
    'value')

  # == Constants == #
  KIND = KEY_KIND
  ANCESTOR = KEY_ANCESTOR

  def __init__(self, value,
                      AND=None,
                      OR=None,
                      _type=KEY_KIND):

    """ Initialize this ``KeyFilter`` with either ``KIND`` or ``ANCESTOR``
        filter modes and a ``value`` to filter against.

        :param value: Value to filter entity keys against.

        :param AND: Subfilters to chain with a logical ``AND``.

        :param OR: Subfilters to chain with a logical ``OR``.

        :param _type: Type of filter to create, defaults to ``KIND``, meaning it
          is a filter against a key's kind name. The other option is
          ``ANCESTRY``, which filters against a key's ancetry path. """

    from canteen import model

    if not (isinstance(value, (model.Key, model.Model)) or (
            isinstance(value, type) and issubclass(value, model.Model)) or (
            value is None)):
      raise ValueError('`KeyFilter` value must be a `Key`, model class,'
                       ' or `None`. Instead, got: "%s".' % repr(value))

    elif _type is self.KIND:
      # extract kind name
      value = value and (
        value.kind() if not isinstance(value, model.Key) else value.kind)

    elif _type is self.ANCESTOR:
      # extract encoded ancestor
      value = value and (
        value.urlsafe() if (
          isinstance(value, model.Key)) else value.key.urlsafe())

    super(KeyFilter, self).__init__(None, value, AND=AND, OR=OR, type=_type)

  @property
  def generic_name(self):  # pragma: no cover

    """ Return a generic string name for labels including this ``KeyFilter``.

        :returns: Static string label, depending on filter type. """

    return 'Key' if self.kind is self.KIND else 'Ancestor'


class EdgeFilter(Filter):

  """ Expresses a filter that applies to a ``Vertex`` objects' undirected or
      directed ``Edge`` objects. """

  magic_symbol = 0x4
  items = (
    'kind',
    'operator',
    'tails',
    'value')

  # == Constants == #
  EDGES = EDGES
  NEIGHBORS = NEIGHBORS

  # == Variables == #
  tails = None

  def __init__(self, value,
                      tails=None,
                      AND=None,
                      OR=None,
                      type=EDGES):

    """ Initialize this ``EdgeFilter`` with either ``EDGES`` or ``NEIGHBORS``
        filter modes and a ``value`` to filter against.

        :param value: Value to filter relationships against.

        :param tails: If this is a query for directed edges, this should be
          ``True`` or ``False`` (for whether *heads* or *tails* are desired).
          Otherwise, if it is ``None`` (the default), this implies a query for
          undirected edges.

        :param AND: Subfilters to chain with a logical ``AND``.

        :param OR: Subfilters to chain with a logical ``OR``.

        :param type: Type of filter to create, defaults to ``KIND``, meaning it
          is a filter against a key's kind name. The other option is
          ``ANCESTRY``, which filters against a key's ancetry path. """

    self.tails = tails
    super(EdgeFilter, self).__init__(None, value, type=type, operator=CONTAINS)

  @property
  def generic_name(self):

    """ Return a generic string name for labels including this ``EdgeFilter``.

        :returns: Static string label, depending on filter type. """

    return 'Edges' if self.kind is self.EDGES else 'Neighbors'


class Sort(QueryComponent):

  """ Expresses a directive to sort resulting entities by a property in a given
      direction. """

  magic_symbol = 0x5
  items = (
    'kind',
    'operator',
    'target')

  ## == Sort Orders == ##
  ASC = ASCENDING = ASC
  DSC = DESCENDING = DSC

  def __init__(self, prop, type=PROPERTY, operator=ASC):

    """ Initialize this :py:class:`Sort`.

        :param prop: Subject property to sort upon.

        :param type: Type of sort to apply, defaults to a ``PROPERTY``-based
          sort, which sorts upon property values.

        :param operator: Either ascending (``ASC`` or ``ASCENDING`` global
          symbols) or descending (``DSC`` or ``DESCENDING`` global symbols). """

    self.target, self.kind, self.operator = prop, type, operator

  def __repr__(self):

    """ Generate a string representation of this :py:class:`Sort`.

        :returns: Pleasant string representation of this ``Sort``, formatted
          like ``Sort(target, operator)``. """

    return 'Sort(%s, %s)' % (self.target.name, self.operator)
