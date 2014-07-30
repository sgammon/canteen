# -*- coding: utf-8 -*-

'''

  canteen: msgpack protocol
  ~~~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import json

# canteen base & core
from canteen.core import runtime
from canteen.base import protocol


## Globals
_content_types = (
  'application/msgpack',
  'application/x-msgpack'
)


with runtime.Library('msgpack') as (library, msgpack):
  with runtime.Library('protorpc') as (library, protorpc):

    # submodules
    protojson = library.load('protojson')  # used for structure


    @protocol.Protocol.register('msgpack', _content_types)
    class Msgpack(protocol.Protocol, protojson.ProtoJson):

      '''  '''

      def encode_message(self, message):

        '''  '''

        message.check_initialized()

        # simple extraction
        _packed = {}
        for field in message.all_fields():
          value = getattr(message, field.name)
          if value is not None:
            _packed[field.name] = value

        return msgpack.packb(_packed)

      def decode_message(self, message_type, encoded_message):

        '''  '''

        # garbage in, garbage out
        if not encoded_message.strip():  # pragma: no cover
          return message_type()

        dictionary = msgpack.unpackb(encoded_message)
        message = self._ProtoJson__decode_dictionary(message_type, dictionary)
        message.check_initialized()
        return message
