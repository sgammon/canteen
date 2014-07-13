# -*- coding: utf-8 -*-

'''

  base protocol tests
  ~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# testing
from canteen import test

# base protocol
from canteen.base import protocol


class SomeValidProtocol(protocol.Protocol):

  ''' I am a valid, registered protocol '''

  def encode_message(self, message): pass
  def decode_message(self, type, encoded): pass


class BaseProtocolTest(test.FrameworkTest):

  ''' Tests `base.protocol`. '''

  def _make_protocol(self, valid=True):

    ''' Build a quick mock Protocol '''

    class SomeProtocol(protocol.Protocol):

      ''' I am a valid, registered protocol '''

      if valid:
        def encode_message(self, message): pass
        def decode_message(self, type, encoded): pass
      else:
        def not_encode_message(self, message): pass
        def not_decode_message(self, type, encoded): pass

    return SomeProtocol

  def test_base_protocol(self):

    ''' Test that `base` exports `Protocol` '''

    assert hasattr(protocol, 'Protocol')

  def test_protocol_abstract(self):

    ''' Test that `Protocol` is abstract '''

    with self.assertRaises(TypeError):
      self._make_protocol(valid=False)()

  def test_protocol_extend(self):

    ''' Test that `Protocol` can be extended '''

    self._make_protocol()()

  def test_protocol_register(self):

    ''' Test that `Protocol` registers properly '''

    # simulate decorator
    protocol.Protocol.register('randorpc', (
      'application/rando',
      'application/x-rando'
    ))(SomeValidProtocol)

  def test_protocol_all(self):

    ''' Test that `Protocol.all` iterates over registered protocols '''

    # simulate decorator
    protocol.Protocol.register('randorpc', (
      'application/rando',
      'application/x-rando'
    ))(SomeValidProtocol)

    all_protocols = [p for p in protocol.Protocol.all]
    assert SomeValidProtocol in all_protocols

  def test_protocol_mapping(self):

    ''' Test that `Protocol.mapping` returns a proper type=>protocol
        mapping '''

    # simulate decorator
    protocol.Protocol.register('randorpc', (
      'application/rando',
      'application/x-rando'
    ))(SomeValidProtocol)

    map = protocol.Protocol.mapping

    assert isinstance(*(
      map.lookup_by_name('randorpc').protocol, SomeValidProtocol))

    assert isinstance(*(
      map.lookup_by_content_type('application/rando').protocol,
      SomeValidProtocol))
