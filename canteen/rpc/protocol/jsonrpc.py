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

# canteen RPC
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


@Protocol.register('jsonrpc', _content_types)
class JSONRPC(Protocol):

  '''  '''

  class JSONMessageCodec(object):

    '''  '''

    pass

  def encode_message(self, message):

    '''  '''

    import pdb; pdb.set_trace()

  def decode_message(self, message_type, encoded_message):

    '''  '''

    import pdb; pdb.set_trace()
