# -*- coding: utf-8 -*-

'''

  canteen RPC: protocol
  ~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import json

# canteen base & core
from canteen.core import runtime
from canteen.base.protocol import Protocol


## Globals
_content_types = (
  'application/json',
  'application/x-javascript',
  'text/javascript',
  'text/x-javascript',
  'text/x-json',
  'text/json'
)


with runtime.Library('protorpc') as (library, protorpc):

  # submodules
  protojson = library.load('protojson')


  @Protocol.register('jsonrpc', _content_types)
  class JSONRPC(Protocol, protojson.ProtoJson):

    '''  '''

    class JSONMessageCodec(protojson.MessageJSONEncoder):

      '''  '''

      pass

    def encode_message(self, message):

      '''  '''

      return protojson.ProtoJson().encode_message(message)

    def decode_message(self, message_type, encoded_message):

      '''  '''

      return protojson.ProtoJson().decode_message(message_type, encoded_message)
