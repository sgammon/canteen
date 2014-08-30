# -*- coding: utf-8 -*-

"""

  JSON protocol tests
  ~~~~~~~~~~~~~~~~~~~

  tests canteen's builtin JSON RPC protocol.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

"""

# stdlib
import json

# canteen core
from canteen.core import Library

# canteen testing
from canteen.test import FrameworkTest


with Library('protorpc', strict=True) as (library, protorpc):

  # load messages library
  messages = library.load('messages')

  # JSON protocol
  from canteen.rpc.protocol import json as jsonrpc


  class SampleMessage(messages.Message):

    """ Sample ProtoRPC message. """

    string = messages.StringField(1)
    integer = messages.IntegerField(2)


  ## JSONProtocolTests
  # Tests the JSON-based RPC protocol.
  class JSONProtocolTests(FrameworkTest):

    """ Tests `rpc.protocol.json.JSON` """

    def test_json_construct(self):

      """ Test basic construction of JSON RPC protocol """

      jsonrpc.JSON()  # yep just that

    def test_json_encode_message(self):

      """ Test encoding RPC messages in JSON """

      # prepare message
      msg = SampleMessage(string='hi', integer=5)
      protocol = jsonrpc.JSON()

      # encode message
      result = protocol.encode_message(msg)

      # decode and test
      inflated = json.loads(result)

      # interrogate
      assert 'string' in inflated
      assert 'integer' in inflated
      assert inflated['string'] == 'hi'
      assert inflated['integer'] == 5

      return result, protocol

    def test_json_decode_message(self):

      """ Test decoding RPC messages from JSON """

      # prepare message
      encoded, protocol = self.test_json_encode_message()

      # decode serialized body
      decoded = protocol.decode_message(SampleMessage, encoded)

      # interrogate
      assert decoded.string == 'hi'
      assert decoded.integer == 5
