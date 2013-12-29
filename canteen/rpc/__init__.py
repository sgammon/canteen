# -*- coding: utf-8 -*-

'''

  canteen: RPC
  ~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''


# stdlib
import os
import time
import json

# canteen
from canteen import core
from canteen import base
from canteen import util
from canteen import model

# canteen core
from canteen.core import meta
from canteen.core import injection

# canteen util
from canteen.util import debug
from canteen.util import decorators
from canteen.util import struct as datastructures


with core.Library('protorpc', strict=True) as (protorpc, library):

  #### ==== Dependencies ==== ####

  # remote / message packages
  from protorpc import remote as premote
  from protorpc import registry as pregistry
  from protorpc.remote import method as proto_method
  from protorpc.remote import Service as ProtoService

  # message packages
  from protorpc import messages as pmessages
  from protorpc.messages import Field as ProtoField
  from protorpc.messages import Message as ProtoMessage

  # message types
  from protorpc import message_types as pmessage_types
  from protorpc.message_types import VoidMessage as ProtoVoidMessage


  #### ==== Message Fields ==== ####

  ## VariantField - a hack that allows a fully-variant field in ProtoRPC message classes.
  class VariantField(ProtoField):

      ''' Field definition for a completely variant field. '''

      VARIANTS = frozenset([pmessages.Variant.DOUBLE, pmessages.Variant.FLOAT, pmessages.Variant.BOOL,
                            pmessages.Variant.INT64, pmessages.Variant.UINT64, pmessages.Variant.SINT64,
                            pmessages.Variant.INT32, pmessages.Variant.UINT32, pmessages.Variant.SINT32,
                            pmessages.Variant.STRING, pmessages.Variant.MESSAGE, pmessages.Variant.BYTES, pmessages.Variant.ENUM])

      DEFAULT_VARIANT = pmessages.Variant.STRING

      type = (int, long, bool, basestring, dict, pmessages.Message)


  #### ==== Message Classes ==== ####

  ## Key - valid as a request or a response, specifies an apptools model key.
  class Key(ProtoMessage):

      ''' Message for a :py:class:`apptools.model.Key`. '''

      encoded = pmessages.StringField(1)  # encoded (`urlsafe`) key
      kind = pmessages.StringField(2)  # kind name for key
      id = pmessages.StringField(3)  # integer or string ID for key
      namespace = pmessages.StringField(4)  # string namespace for key
      parent = pmessages.MessageField('Key', 5)  # recursive key message for parent


  ## Echo - valid as a request as a response, simply defaults to 'Hello, world!'. Mainly for testing.
  class Echo(ProtoMessage):

      ''' I am rubber and you are glue... '''

      message = pmessages.StringField(1, default='Hello, world!')


  ## expose message classes alias
  messages = datastructures.WritableObjectProxy(**{

      # apptools-provided messages
      'Key': Key,  # message class for an apptools model key
      'Echo': Echo,  # echo message defaulting to `hello, world` for testing

      # builtin messages
      'Message': ProtoMessage,  # top-level protorpc message class
      'VoidMessage': ProtoVoidMessage,  # top-level protorpc void message

      # specific types
      'Enum': pmessages.Enum,  # enum descriptor / definition class
      'Field': pmessages.Field,  # top-level protorpc field class
      'FieldList': pmessages.FieldList,  # top-level protorpc field list class

      # field types
      'VariantField': VariantField,  # generic hold-anything property (may cause serializer problems - be careful)
      'BooleanField': pmessages.BooleanField,  # boolean true/false field
      'BytesField': pmessages.BytesField,  # low-level binary-safe string field
      'EnumField': pmessages.EnumField,  # field for referencing an :py:class:`pmessages.Enum` class
      'FloatField': pmessages.FloatField,  # field for a floating point number
      'IntegerField': pmessages.IntegerField,  # field for an integer
      'MessageField': pmessages.MessageField,  # field for a sub-message (:py:class:`pmessages.Message`)
      'StringField': pmessages.StringField,  # field for unicode or ASCII strings
      'DateTimeField': pmessage_types.DateTimeField  # field for containing datetime types

  })


  class ServiceHandler(base.Handler):

    '''  '''

    pass


  class Service(object):

    '''  '''

    __owner__, __metaclass__ =  "Service", injection.Compound


  class remote(object):

    '''  '''

    name = None  # string name for target
    config = None  # config items for target

    def __init__(self, name, expose='public', **config):

      '''  '''

      if expose != 'public':
        raise NotImplementedError('Private remote methods are not yet implemented.')
      print "registering %s..." % name

    @classmethod
    def public(cls, name, **config):

      '''  '''

      return cls(name, expose='public', **config)

    @classmethod
    def private(cls, name, **config):

      '''  '''

      return cls(name, expose='private', **config)

    def __call__(self, target):

      '''  '''

      print "caught %s..." % str(target)
      return target
