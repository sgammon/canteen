# -*- coding: utf-8 -*-

"""

  msgpack RPC protocol
  ~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# canteen base & core
from canteen.core import runtime
from canteen.base import protocol


## Globals
_content_types = (
  'application/msgpack',
  'application/x-msgpack')


with runtime.Library('msgpack') as (msglib, msgpack):
  with runtime.Library('protorpc') as (protolib, protorpc):

    # submodules
    protojson = protolib.load('protojson')
    messages = protolib.load('messages')


    @protocol.Protocol.register('msgpack', _content_types)
    class Msgpack(protocol.Protocol, protojson.ProtoJson):

      """  """

      def encode_message(self, message):

        """  """

        message.check_initialized()

        def _walk_struct(m):

          """ recursively encode msgpack """

          # simple extraction
          _packed = {}
          for field in m.all_fields():
            value = getattr(m, field.name)
            if value is not None:
              if isinstance(value, messages.Message):
                _packed[field.name] = _walk_struct(value)
              else:
                _packed[field.name] = value
          return _packed
        return msgpack.packb(_walk_struct(message))

      def decode_message(self, message_type, encoded_message):

        """  """

        # garbage in, garbage out
        if not encoded_message.strip():  # pragma: no cover
          return message_type()

        dictionary = msgpack.unpackb(encoded_message)
        message = self._ProtoJson__decode_dictionary(message_type, dictionary)
        message.check_initialized()
        return message
