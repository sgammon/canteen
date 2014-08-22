# -*- coding: utf-8 -*-

'''

  msgpack protocol tests
  ~~~~~~~~~~~~~~~~~~~~~~

  tests canteen's builtin msgpack RPC protocol.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

'''

# canteen core
from canteen.core import Library

# canteen testing
from canteen.test import FrameworkTest



with Library('msgpack') as (mlibrary, msgpack):

  import msgpack  # force re-import

  with Library('protorpc', strict=True) as (plibrary, protorpc):

    # load messages library
    messages = plibrary.load('messages')

    # msgapck protocol
    from canteen.rpc.protocol import msgpack as msgpackrpc


    class SampleMessage(messages.Message):

      ''' Sample ProtoRPC message. '''

      string = messages.StringField(1)
      integer = messages.IntegerField(2)


    ## MsgpackProtocolTests
    # Tests the msgpack-based RPC protocol.
    class MsgpackProtocolTests(FrameworkTest):

      ''' Tests `rpc.protocol.msgpack.Msgpack` '''

      def test_msgpack_construct(self):

        ''' Test basic construction of msgpack RPC protocol '''

        msgpackrpc.Msgpack()  # yep just that

      def test_msgpack_encode_message(self):

        ''' Test encoding RPC messages in msgpack '''

        # prepare message
        msg = SampleMessage(string='hi', integer=5)
        protocol = msgpackrpc.Msgpack()

        # encode message
        result = protocol.encode_message(msg)

        # decode and test
        inflated = msgpack.unpackb(result)

        # interrogate
        assert 'string' in inflated
        assert 'integer' in inflated
        assert inflated['string'] == 'hi'
        assert inflated['integer'] == 5

        return result, protocol

      def test_msgpack_decode_message(self):

        ''' Test decoding RPC messages from msgpack '''

        # prepare message
        encoded, protocol = self.test_msgpack_encode_message()

        # decode serialized body
        decoded = protocol.decode_message(SampleMessage, encoded)

        # interrogate
        assert decoded.string == 'hi'
        assert decoded.integer == 5
