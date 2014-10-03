# -*- coding: utf-8 -*-

"""

  protorpc model extensions
  ~~~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import datetime

# adapter API
from .abstract import KeyMixin
from .abstract import ModelMixin

# canteen util
from canteen.util import struct as datastructures


## == protorpc support == ##
try:
  # force absolute import to prevent infinite recursion
  protorpc = __import__('protorpc', tuple(), tuple(), [], 0)

except ImportError as e:  # pragma: no cover
  # flag as unavailable
  _PROTORPC, _root_message_class = False, object

else:
  # extended imports (must be absolute)
  _p = __import__('protorpc', [], [], ['messages', 'message_types'], 0)
  pmessages = getattr(_p, 'messages')
  pmessage_types = getattr(_p, 'message_types')

  # constants
  _model_impl = {}
  _field_kwarg = 'field'
  _PROTORPC, _root_message_class = True, pmessages.Message

  # map fields to basetypes
  _field_basetype_map = {
    int: pmessages.IntegerField,
    long: pmessages.IntegerField,
    bool: pmessages.BooleanField,
    float: pmessages.FloatField,
    str: pmessages.StringField,
    unicode: pmessages.StringField,
    basestring: pmessages.StringField,
    datetime.time: pmessages.StringField,
    datetime.date: pmessages.StringField,
    datetime.datetime: pmessages.StringField}

  # build quick basetype lookup
  _builtin_basetypes = frozenset(_field_basetype_map.keys())

  # map fields to explicit names
  _field_explicit_map = {
    pmessages.EnumField.__name__: pmessages.EnumField,  # 'EnumField'
    pmessages.BytesField.__name__: pmessages.BytesField,  # 'BytesField'
    pmessages.FloatField.__name__: pmessages.FloatField,  # 'FloatField'
    pmessages.StringField.__name__: pmessages.StringField,  # 'StringField'
    pmessages.IntegerField.__name__: pmessages.IntegerField,  # 'IntegerField'
    pmessages.BooleanField.__name__: pmessages.BooleanField}  # 'BooleanField'

  # build quick builtin lookup
  _builtin_fields = frozenset(_field_explicit_map.keys())


  # recursive message builder
  def build_message(_model):

    """ Recursively builds a new `Message` class dynamically from a canteen
        :py:class:`model.Model`. Properties are converted to their
        :py:mod:`protorpc` equivalents and factoried into a full
        :py:class:`messages.Message` class.

        :param _model: Model class to convert to a
          :py:class:`protorpc.messages.Message` class.

        :raises TypeError: In the case of an unidentified or unknown
          property basetype.
        :raises ValueError: In the case of a missing implementation field
          or serialization error.

        :returns: Constructed (but not instantiated)
          :py:class:`protorpc.messages.Message` class. """

    # must nest import to avoid circular dependencies
    from canteen import rpc
    from canteen import model

    # provision field increment and message map
    _field_i, _model_message = 1, {'__module__': _model.__module__}

    # grab lookup and property dict
    lookup, property_map = _model.__lookup__, {}

    # add key submessage
    _model_message['key'] = pmessages.MessageField(rpc.Key, _field_i)

    # build fields from model properties
    for name in lookup:

      # init args and kwargs
      _pargs, _pkwargs = [], {}

      # grab property class
      prop = property_map[name] = _model.__dict__[name]

      # copy in default if field has explicit default value
      if prop.default != prop.sentinel:
        _pkwargs['default'] = prop.default

      # map in required and repeated kwargs
      _pkwargs['required'], _pkwargs['repeated'] = (
        prop.required, prop.repeated)

      # check for explicit field
      if _field_kwarg in prop.options:

        # grab explicit field, if any
        explicit = prop.options.get(_field_kwarg, datastructures.EMPTY)

        # explcitly setting `False` or `None` means skip this field
        if explicit is False or explicit is None:  # pragma: no cover
          continue  # continue without incrementing: skipped field

        # if it's a tuple, it's a name/args/kwargs pattern
        if not isinstance(explicit, (basestring, tuple)):
          context = (name, _model.kind(), type(explicit))
          raise TypeError('Invalid type found for explicit message field'
                          ' implementation binding - property \"%s\" of model'
                          ' \"%s\" cannot bind to field of type \"%s\".'
                          ' A basestring field name or tuple of'
                          ' (name, *args, <**kwargs>) was expected.' % context)

        elif isinstance(explicit, tuple):

          # two indicates name + args
          if len(explicit) == 2:  # name, *args
            explicit, _pargs = explicit
            _pkwargs = {}

          # three indicates name + args + kwargs
          elif len(explicit) == 3:  # name, *args, **kwargs
            explicit, _pargs, _pkwargs = explicit

        # grab explicit field (if it's not a tuple it's a basestring)
        if explicit in _builtin_fields:

          # flatten arguments, splice in ID
          if len(_pargs) > 0:
            if not isinstance(_pargs, list):
              _pargs = [i for i in _pargs]

            _field_i += 1
            _pargs.append(_field_i)
            _pargs = tuple(_pargs)
          else:
            # shortcut: replace it if there's no args
            _field_i += 1
            _pargs = (_field_i,)

          # factory field
          _model_message[name] = (
            _field_explicit_map[explicit](*_pargs, **_pkwargs))
          continue

        else:
          # raise a `ValueError` in the case of an invalid explicit field name
          raise ValueError("No such message implementation"
                           " field: \"%s\"." % name)

      # check variant by dict
      if prop.basetype == dict:
        _field_i += 1
        _model_message[name] = rpc.VariantField(_field_i)
        continue

      # check recursive submodels
      elif isinstance(prop.basetype, type(type)) and (
        issubclass(prop.basetype, model.AbstractModel)):

        # shortcut: `model.Model` for `VariantField`s
        if prop.basetype is model.Model:

          ## general, top-level `Model` means a variant field
          _field_i += 1
          _model_message[name] = rpc.VariantField(_field_i)
          continue

        # recurse - it's a model class
        _field_i += 1
        _pargs.append(prop.basetype.to_message_model())
        _pargs.append(_field_i)

        # factory
        _model_message[name] = pmessages.MessageField(*_pargs, **_pkwargs)
        continue

      # handle int/str combination fields
      elif isinstance(prop.basetype, tuple) and (
            prop.basetype in ((int, str), (str, int))):

        # build field and advance
        _field_i += 1
        _pargs.append(_field_i)
        _model_message[name] = rpc.StringOrIntegerField(*_pargs, **_pkwargs)
        continue

      # check for keys (implemented with `basestring` for now)
      elif issubclass(prop.basetype, model.AbstractKey):

        # build field and advance
        _field_i += 1
        _pargs.append(rpc.Key)
        _pargs.append(_field_i)
        _model_message[name] = pmessages.MessageField(*_pargs)
        continue

      # check for enums
      elif issubclass(prop.basetype, datastructures.BidirectionalEnum):

        # build enum class, field, and advance
        _field_i += 1
        _enum = pmessages.Enum.__metaclass__.__new__(*(
          pmessages.Enum.__metaclass__,
          prop.basetype.__name__,
          (pmessages.Enum,),
          {k: v for k, v in prop.basetype}))
        _pargs.append(_enum)
        _pargs.append(_field_i)

        if prop.default not in (
            model.Property.sentinel, None):  # pragma: no cover
          _pkwargs['default'] = (
            prop.basetype.reverse_resolve(prop.default))

        _model_message[name] = pmessages.EnumField(*_pargs, **_pkwargs)
        continue

      # check builtin basetypes
      elif prop.basetype in _builtin_basetypes:

        # build field and advance
        _field_i += 1
        _pargs.append(_field_i)
        if 'default' in _pkwargs and prop.basetype in (
              datetime.datetime, datetime.date):
          del _pkwargs['default']  # no support for defaults on date types
        _model_message[name] = (
          _field_basetype_map[prop.basetype](*_pargs, **_pkwargs))
        continue

      # check for builtin hook for message implementation
      elif hasattr(prop.basetype, '__message__'):

        # delegate field and advance
        _field_i += 1
        _pargs.append(_field_i)
        _model_message[name] = prop.basetype.__message__(*_pargs, **_pkwargs)
        continue

      else:  # pragma: no cover
        context = (name, _model.kind(), prop.basetype)
        raise ValueError("Could not resolve proper serialization for property"
                         " \"%s\" of model \"%s\" (found basetype \"%s\")." % (
                          context))

    # construct message class on-the-fly
    return type(_model.kind(), (pmessages.Message,), _model_message)


  ## ProtoRPCKey
  class ProtoRPCKey(KeyMixin):

    """ Adapt `Key` classes to ProtoRPC messages. """

    def to_message(self, flat=False, encoded=False):

      """ Convert a `Key` instance to a ProtoRPC `Message` instance.

          :returns: Constructed :py:class:`protorpc.Key` message object. """

      from canteen import rpc

      args = {
        'id': self.id,
        'kind': self.kind,
        'encoded': self.urlsafe()}

      if self.parent:
        if encoded:
          # indication from outer method that we should only encode
          return rpc.Key(**args)  # pragma: no cover
        args['parent'] = self.parent.to_message(not flat, flat)

      return rpc.Key(**args)

    @classmethod
    def to_message_model(cls):

      """ Return a schema for a `Key` instance in ProtoRPC `Message` form.

          :returns: Vanilla :py:class:`protorpc.Key` class. """

      from canteen import rpc
      return rpc.Key

    @classmethod
    def from_message(cls, key_message):

      """  """

      parent = cls.from_message(key_message.parent) if (
        key_message.parent
      ) else None

      # decode recursively for parent key, if specified
      return cls(key_message.kind, key_message.id, parent=parent)


  ## ProtoRPCModel
  class ProtoRPCModel(ModelMixin):

    """ Adapt Model classes to ProtoRPC messages. """

    def to_message(self, *args, **kwargs):

      """ Convert a `Model` instance to a ProtoRPC `Message` class.

          :param args: Positional arguments to pass to
            :py:meth:`Model.to_dict`.

          :param kwargs: Keyword arguments to pass to
            :py:meth:`Model.to_dict`.

          :returns: Constructed and initialized :py:class:`protorpc.Message`
            object. """

      # must import inline to avoid circular dependency
      from canteen import rpc
      from canteen import model

      values = {}
      for prop, value in self.to_dict(*args,
                                      convert_keys=False, **kwargs).items():

        # convert keys => urlsafe
        if isinstance(value, (model.Key, model.VertexKey, model.EdgeKey)):
          values[prop] = rpc.Key(
            id=value.id,
            kind=value.kind,
            encoded=value.urlsafe())
          continue

        # convert date/time/datetime => string
        if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
          values[prop] = value.isoformat()  # pragma: no cover
          continue  # pragma: no cover

        values[prop] = value  # otherwise, just set it

      if self.key:
        return self.__class__.to_message_model()(
          key=self.key.to_message(), **values)

      def _check_value(item):

        """ Checks for invalid ProtoRPC values. """

        key, value = item

        if isinstance(value, list) and len(value) == 0:
          return False  # pragma: no cover
        return True

      filtered = filter(_check_value, values.iteritems())
      return self.__class__.to_message_model()(**dict(filtered))

    @classmethod
    def to_message_model(cls):

      """ Convert a `Model` class to a ProtoRPC `Message` class. Delegates
          to :py:func:`build_message`, see docs there for exceptions raised
          (:py:exc:`TypeError` and :py:exc:`ValueError`).

          :returns: Constructed (but not initialized) dynamically-build
            :py:class:`message.Message` class corresponding to
            the current model (``cls``). """

      global _model_impl

      # check global model=>message implementation cache
      if (cls, cls.__lookup__) not in _model_impl:

        # build message class
        _model_impl[(cls, cls.__lookup__)] = build_message(cls)

      # return from cache
      return _model_impl[(cls, cls.__lookup__)]

    @classmethod
    def from_message(cls, message):

      """ DOCSTRING """

      # create an empty model, loading its key
      # (if present, which it will be if this is coming from `to_message`)
      key = cls.__keyclass__.from_message(message.key) if (
        hasattr(message, 'key') and message.key is not None) else None

      model = cls(key=key) if key else cls()

      # decode field values
      for field, value in ((
        k.name, message.get_assigned_value(k.name)) for k in (
            message.all_fields())):

        if field is not 'key':
          model[field] = value

      return model
