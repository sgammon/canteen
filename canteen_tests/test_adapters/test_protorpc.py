# -*- coding: utf-8 -*-

"""

  protorpc adapter tests
  ~~~~~~~~~~~~~~~~~~~~~~

  tests integration between canteen's model layer and
  Google's :py:mod:`protorpc`.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import datetime

# testing
from canteen import rpc
from canteen import test
from canteen import model
from canteen import struct

# protorpc
from protorpc import messages

# adapter & exceptions
from canteen.model import exceptions
from canteen.model.adapter import protorpc


class ProtoRPCAdapterModuleTest(test.FrameworkTest):

  """ Tests the ProtoRPC model adapter """

  def test_module_globals(self):

    """ Test ProtoRPC adapter globals """

    assert hasattr(protorpc, 'protorpc')
    assert hasattr(protorpc, 'pmessages')
    assert hasattr(protorpc, 'pmessage_types')
    assert hasattr(protorpc, 'build_message')
    assert hasattr(protorpc, 'ProtoRPCKey')
    assert hasattr(protorpc, 'ProtoRPCModel')

  def test_build_message(self):

    """ Test `build_message` with a basic `Model` """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'integer')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi', integer=5)
    message = message_class(string='hi', integer=5)

    assert _model.string == message.string
    assert _model.integer == message.integer

  def test_build_message_default(self):

    """ Test `build_message` with a property that has a default value """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int, {'default': 10}

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'integer')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi')
    message = message_class(string='hi')

    assert _model.string == message.string
    assert _model.integer == message.integer

  def test_build_message_required(self):

    """ Test `build_message` with a required property """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int, {'required': True}

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'integer')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi')
    message = message_class(string='hi')

    assert _model.string == message.string
    assert _model.integer == message.integer

    with self.assertRaises(exceptions.PropertyRequired):
      _model.put()

    with self.assertRaises(messages.ValidationError):
      message.check_initialized()

  def test_build_message_repeated(self):

    """ Test `build_message` with a repeated property """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int, {'repeated': True}

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'integer')
    assert message_class.integer.repeated is True
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi', integer=[1, 2, 3])
    message = message_class(string='hi', integer=[1, 2, 3])

    assert _model.string == message.string
    assert type(_model.integer) is list
    assert type(message.integer) is messages.FieldList
    assert len(_model.integer) == 3 and len(message.integer) == 3

  def test_build_message_explicit_implementation_field(self):

    """ Test `build_message` with a valid explicit implementation field """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = float, {'field': 'IntegerField'}

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'integer')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi', integer=5.5)
    message = message_class(string='hi', integer=5)

    assert _model.string == message.string
    assert isinstance(_model.integer, float)
    assert isinstance(message.integer, int)

  def test_build_message_invalid_implementation_field(self):

    """ Test `build_message` with an invalid explicit implementation field """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int, {'field': 'NoSuchField'}

    with self.assertRaises(ValueError):
      protorpc.build_message(SimpleModel)

  def test_build_message_skip_field(self):

    """ Test `build_message` with an indication to skip a field """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = float, {'field': False}

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert not hasattr(message_class, 'integer')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi', integer=5.5)
    message = message_class(string='hi')

    assert _model.string == message.string
    with self.assertRaises(AttributeError):
      message.integer

  def test_build_message_explicit_field_args(self):

    """ Test `build_message` with implementation field args """


    class SimpleEnum(messages.Enum):

      """ Enumerates colors! """

      RED = 0x0
      BLUE = 0x1
      GREEN = 0x2


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      color = basestring, {'field': ('EnumField', (SimpleEnum,))}

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'color')
    assert message_class.color.type is SimpleEnum

  def test_build_message_with_enum(self):

    """ Test `build_message` with a message that contains an enum """


    class Color(struct.BidirectionalEnum):

      """ Sample enumeration of a bunch of colors. """

      BLUE = 0x0
      RED = 0x1
      GREEN = 0x2


    class SomeModel(model.Model):

      """ Something involving colors. """

      color = Color
      name = str

    message_class = protorpc.build_message(SomeModel)

    assert hasattr(message_class, 'color')
    assert hasattr(message_class, 'name')
    assert message_class.color.type.BLUE is Color.BLUE

  def test_build_message_explicit_field_args_kwargs(self):

    """ Test `build_message` with an implementation of field args + kwargs """


    class SimpleEnum(messages.Enum):

      """ Enumerates colors! """

      RED = 0x0
      BLUE = 0x1
      GREEN = 0x2


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      color = basestring, {
        'field': ('EnumField', (SimpleEnum,), {'default': SimpleEnum.RED})}

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'color')
    assert message_class.color.type is SimpleEnum
    assert message_class().color is SimpleEnum.RED

  def test_build_message_bogus_explicit_field(self):

    """ Test `build_message` with a bogus field value """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      color = basestring, {'field': 5.5}

    with self.assertRaises(TypeError):
      protorpc.build_message(SimpleModel)

  def test_build_message_submodel(self):

    """ Test `build_message` with an embedded submodel """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int


    class SimpleContainer(model.Model):

      """ Simple container message """

      model = SimpleModel

    message_class = protorpc.build_message(SimpleContainer)

    assert hasattr(message_class, 'model')
    assert message_class.__name__ == SimpleContainer.kind()
    assert message_class.model.message_type.__name__ == SimpleModel.kind()

  def test_build_message_variant(self):

    """ Test `build_message` with a variant property """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int
      data = dict

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'integer')
    assert hasattr(message_class, 'data')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi', integer=5, data={'hi': 'sup'})
    message = message_class(string='hi', integer=5, data={'hi': 'sup'})

    assert _model.string == message.string
    assert _model.integer == message.integer
    assert _model.data['hi'] == message.data['hi']

  def test_build_message_variant_vanilla_model(self):

    """ Test `build_message` with a variant property (by vanilla `Model`) """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int
      data = model.Model

    some_model = SimpleModel(string='hithere')
    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'integer')
    assert hasattr(message_class, 'data')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi', integer=5, data=some_model)
    message = message_class(string='hi', integer=5, data=some_model.to_dict())

    assert _model.string == message.string
    assert _model.integer == message.integer
    assert _model.data.string == message.data['string']

  def test_build_message_key(self):

    """ Test `build_message` with a `Key` property """


    class SimpleModel(model.Model):

      """ Simple model message """

      string = basestring
      integer = int
      ref = model.Key

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert hasattr(message_class, 'integer')
    assert hasattr(message_class, 'ref')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='hi', integer=5, ref=model.Key('hi', 1))
    message = message_class(string='hi', integer=5, ref=model.Key('hi', 1).to_message())
    _msg_from_obj = _model.to_message()

    assert _model.string == message.string
    assert _model.integer == message.integer
    assert _model.ref.urlsafe() == message.ref.encoded
    assert _msg_from_obj.ref.encoded == _model.ref.urlsafe()
    assert _msg_from_obj.ref.id == 1

  def test_build_message_hook(self):

    """ Test `build_message` with a target object hook """

    class SomeProperty(model.Property):

      """ Simple property with __message__ hook """

      _basetype = basestring

      @classmethod
      def __message__(cls, *args, **kwargs):

        """ Return an IntegerField implementation... """

        return messages.IntegerField(*args, **kwargs)

    class SimpleModel(model.Model):

      """ Simple model message """

      string = SomeProperty

    message_class = protorpc.build_message(SimpleModel)

    assert hasattr(message_class, 'string')
    assert message_class.__name__ == SimpleModel.kind()

    _model = SimpleModel(string='5')  # it's a basestring...
    message = message_class(string=5)  # jk its an int! lol

    assert int(_model.string) == message.string


class ProtoRPCAdaptedKeyTest(test.FrameworkTest):

  """ Tests for the ProtoRPC `Key` mixin """

  def test_key_to_message(self):

    """ Test converting a `Key` to a message """

    key = model.Key('Hi', 5)
    message = key.to_message()

    assert message.id == key.id
    assert message.kind == key.kind
    assert message.encoded == key.urlsafe()
    assert isinstance(message, rpc.Key)

  def test_key_with_name_to_message(self):

    """ Test converting a `Key` with a parent to a message """

    key = model.Key('Hi', 'there')
    message = key.to_message()

    assert message.id == key.id
    assert message.kind == key.kind
    assert message.encoded == key.urlsafe()
    assert isinstance(message, rpc.Key)

  def test_key_with_parent_to_message(self):

    """ Test converting a `Key` with a parent to a message """

    key = model.Key('Hi', 'there', parent=model.Key('Sup', 'hey'))
    message = key.to_message()

    assert message.id == key.id
    assert message.kind == key.kind
    assert message.encoded == key.urlsafe()
    assert message.parent.id == key.parent.id
    assert message.parent.kind == key.parent.kind
    assert message.parent.encoded == key.parent.urlsafe()
    assert isinstance(message, rpc.Key)
    assert isinstance(message.parent, rpc.Key)

  def test_key_with_ancestry_to_message(self):

    """ Test converting a `Key` with two parent generations to a message """

    key = model.Key('Hi', 'there', parent=model.Key('Sup', 'hey', parent=(
      model.Key('Hola', 'senor')
    )))

    message = key.to_message()

    assert isinstance(message, rpc.Key)
    assert isinstance(message.parent, rpc.Key)
    assert isinstance(message.parent.parent, rpc.Key)

    assert message.id == key.id
    assert message.kind == key.kind
    assert message.encoded == key.urlsafe()
    assert message.parent.id == key.parent.id
    assert message.parent.kind == key.parent.kind
    assert message.parent.encoded == key.parent.urlsafe()
    assert message.parent.parent.id == key.parent.parent.id
    assert message.parent.parent.kind == key.parent.parent.kind
    assert message.parent.parent.encoded == key.parent.parent.urlsafe()

  def test_key_to_message_model(self):

    """ Test converting a `Key` class to a message """

    message_class = model.Key.to_message_model()
    assert message_class.__name__ == model.Key.__name__

    assert hasattr(message_class, 'id')
    assert hasattr(message_class, 'kind')
    assert hasattr(message_class, 'parent')
    assert hasattr(message_class, 'encoded')
    assert hasattr(message_class, 'namespace')

  def test_message_to_key(self):

    """ Test inflating a message to a `Key` instance """

    message_class = model.Key.to_message_model()
    message = message_class(kind='Hi', id=5)

    assert hasattr(message_class, 'id')
    assert hasattr(message_class, 'kind')
    assert hasattr(message_class, 'parent')
    assert hasattr(message_class, 'encoded')
    assert hasattr(message_class, 'namespace')

    assert message.id == 5
    assert message.kind == 'Hi'

    key = model.Key.from_message(message)
    assert key.id == 5
    assert key.kind == 'Hi'

  def test_message_to_key_with_name(self):

    """ Test inflating a message to a `Key` with a string ID """

    message_class = model.Key.to_message_model()
    message = message_class(kind='Hi', id='friend')

    assert hasattr(message_class, 'id')
    assert hasattr(message_class, 'kind')
    assert hasattr(message_class, 'parent')
    assert hasattr(message_class, 'encoded')
    assert hasattr(message_class, 'namespace')

    assert message.id == 'friend'
    assert message.kind == 'Hi'

    key = model.Key.from_message(message)
    assert key.id == 'friend'
    assert key.kind == 'Hi'

  def test_message_to_key_with_parent(self):

    """ Test inflating a message to a `Key` with a parent """

    message_class = model.Key.to_message_model()
    message = message_class(
      kind='Hi',
      id='friend',
      parent=model.Key('Sup', 'homie').to_message())

    assert hasattr(message_class, 'id')
    assert hasattr(message_class, 'kind')
    assert hasattr(message_class, 'parent')
    assert hasattr(message_class, 'encoded')
    assert hasattr(message_class, 'namespace')

    assert message.id == 'friend'
    assert message.kind == 'Hi'

    key = model.Key.from_message(message)
    assert key.id == 'friend'
    assert key.kind == 'Hi'
    assert key.parent.id == 'homie'
    assert key.parent.kind == 'Sup'

  def test_message_to_key_with_ancestry(self):

    """ Test inflating a message to a `Key` with deep ancestry """

    message_class = model.Key.to_message_model()
    message = message_class(
      kind='Hi',
      id='friend',
      parent=model.Key('Sup', 'homie', **{
        'parent': model.Key('Hola', 'senor')
      }).to_message()
    )

    assert hasattr(message_class, 'id')
    assert hasattr(message_class, 'kind')
    assert hasattr(message_class, 'parent')
    assert hasattr(message_class, 'encoded')
    assert hasattr(message_class, 'namespace')

    assert message.id == 'friend'
    assert message.kind == 'Hi'

    key = model.Key.from_message(message)
    assert key.id == 'friend'
    assert key.kind == 'Hi'
    assert key.parent.id == 'homie'
    assert key.parent.kind == 'Sup'
    assert key.parent.parent.id == 'senor'
    assert key.parent.parent.kind == 'Hola'


class ProtoRPCAdaptedModelTests(test.FrameworkTest):

  """ Tests for the ProtoRPC `Model` mixin """

  def test_model_to_message(self):

    """ Test converting a `Model` to a `Message` """


    class TestProtoRPCModel(model.Model):

      """ sample model """

      string = basestring
      number = int
      dt = datetime.datetime

    now = datetime.datetime.now()
    s = TestProtoRPCModel(string='hi', number=5, dt=now)
    m = s.to_message()

    assert m.string == 'hi'
    assert m.number == 5
    assert m.dt == now.isoformat()

    s2 = TestProtoRPCModel(key=model.Key(TestProtoRPCModel, 'sup'),
                           string='hi', number=5, dt=now)
    m2 = s2.to_message()

    assert m2.string == 'hi'
    assert m2.number == 5
    assert m2.dt == now.isoformat()
    assert m2.key.encoded == s2.key.urlsafe()

  """
  def test_model_to_message_model(self):

    ''' Test converting a `Model` class to a `Message` class '''

    pass

  def test_message_to_model(self):

    ''' Test inflating a `Model` from a `Message` '''

    pass
  """
