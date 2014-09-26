# -*- coding: utf-8 -*-

"""

  realtime logic
  ~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import time
import hashlib

# core and utils
from ..base import logic
from ..util import struct
from ..util import decorators


# Globals
_ORIGIN_ENV_ITEM = 'HTTP_ORIGIN'
_SOCKET_KEY_ENV_ITEM = 'HTTP_SEC_WEBSOCKET_KEY'
_FORWARDED_FOR_ENV_ITEM = 'HTTP_X_FORWARDED_FOR'


class RealtimeSocket(object):

  """ Specifies a structure for keeping track of socket details during a
      live realtime communication session. Simple things like the local/remote
      address/port pairs are used to make a socket ID that can be passed around
      and used as a reference. """

  __slots__ = (
    '__id__',  # ID of the socket
    '__state__',  # current state
    '__local__',  # local port pair
    '__remote__',  # remote port pair
    '__runtime__',  # link to current runtime
    '__established__')  # establish timestamp

  class State(struct.BidirectionalEnum):

    """ Enumerates available ``RealtimeSocket`` states, or the phases of a
        realtime communication session. """

    INIT = 0x0
    OPEN = 0x1
    ACTIVE = 0x2
    CLOSED = 0x3
    ERROR = 0x4

  def __init__(self, runtime,
                     local=None,
                     remote=None):

    """ Initialize this ``RemoteSocket`` object with details about the current
        ``runtime`` and the connection's ``local`` and ``remote`` peers.

        :param runtime: Currently-active Canteen runtime.

        :param local: Local (server) address & port pair that is handling the
          connection.

        :param remote: Remote (client) address & port pair that is on the other
          side of the connection. """

    self.__established__ = time.time()

    self.__id__, self.__runtime__ = (
      hashlib.sha1('::'.join((local, remote))).hexdigest(),
      runtime)

    self.__local__, self.__remote__ = local, remote

  def set_state(self, state):

    """ Set the current state of this ``RealtimeSocket``. Available states are
        enumerated in a ``BidirectionalEnum`` at ``self.State``. Current state
        is stored in the object-private ``__state__``.

        :param state: ``State`` to set the current socket to.
        :returns: ``self``, for chainability. """

    return setattr(self, '__state__', state) or self

  def receive(self):

    """ Callable to reach through to the currently-active runtime and attempt
        to receive communication from the client-side of an active realtime
        communication session.

        :returns: Next message from the client (in a blocking/nonblocking way
         depending on the runtime's implementation). """

    return self.__runtime__.receive()

  def send(self, payload):

    """ Send a payload, via the currently-active runtime, to the client-side of
        the current realtime communication session.

        :returns: ``None``. """

    self.__runtime__.send(payload)

  # ~~ accessors ~~ #
  id, state, local, remote, runtime, established = (
    property(lambda self: self.__id__),
    property(lambda self: self.__state__),
    property(lambda self: self.__local__),
    property(lambda self: self.__remote__),
    property(lambda self: self.__runtime__),
    property(lambda self: self.__established__))


@decorators.bind('realtime', namespace=True)
class RealtimeSemantics(logic.Logic):

  """ Provides logic structure to handle realtime-style (acyclic) dispatch
      flows, as opposed to HTTP-style (cyclic) ones. Used in cases like
      WebSockets that provide a live bidirectional link. """

  hint = _SOCKET_KEY_ENV_ITEM

  def stream(self, target, send):

    """ Prepare to consume a stream of packets/messages from ``target``, using
        ``send`` as a callback to transmit messages back to the client.

        Returns a ``responder`` generator that acts as a coroutine-style Python
        generator. Consumes messages via ``send`` and ``yield``s messages to be
        sent.

        :param target: Callable for consuming/receiving/blocking on new data
          from the client.

        :param send: Callable for sending data to the client.

        :returns: Prepared ``responder`` generator. """

    def responder(dispatch):

      """ Inner closure ``responder``, acts as a coroutine-style Python
          generator to consume packets from a realtime-enabled client
          connection, ``dispatch`` for a potential response, and forward
          outbound messages back to the client.

          :param dispatch: Application callable that should handle the inbound
            message, potentially ``yield``ing messages to be sent.

          :returns: Never. """

      while True:
        inbound = (yield)
        if inbound is not None:
          for outbound in dispatch(inbound):
            send(outbound)

    gen = responder(target)
    gen.next()
    return gen

  def on_connect(self, handler):

    """ Top-level ``on_connect`` logic that provides initialization for a
        ``RealtimeSocket`` session.

        :param handler: Active ``RealtimeHandler`` instance that is handling
          this realtime session.

        :returns: :py:class:`RealtimeSocket` instance describing the
          newly-active realtime session. """

    # perform handshake through current runtime
    handler.runtime.handshake(*(
      handler.request.environ[self.hint],
      handler.request.environ.get(_ORIGIN_ENV_ITEM, '')))

    # resolve proxies
    sock = RealtimeSocket(handler.runtime, **{
      'local': handler.request.host,
      'remote': handler.request.remote_addr})

    sock.set_state(sock.State.OPEN)

    # provide to handler
    handler.on_connect()

  def on_message(self, handler, socket):

    """ Top-level ``on_message` logic that provides dispatch for inbound
        realtime messages.

        :param handler: Active ``RealtimeHandler`` instance that is handling
          this realtime session.

        :param socket: Active ``RealtimeSocket`` instance for the currently-
          active realtime session.

        :returns: ``None``, upon connection close. """

    responder = self.stream(handler.on_message, socket.send)
    socket.set_state(socket.State.ACTIVE)

    while True:
      try:
        inbound = socket.receive()
        if inbound: responder.send(inbound)

      except (GeneratorExit, StopIteration):
        break
    self.on_close(handler, socket)

  def on_close(self, handler, socket):

    """ Top-level ``on_close`` logic that provides cleanup logic for realtime
        communication sessions.

        :param handler: Currently-active ``RealtimeHandler`` instance that is
          managing this realtime session.

        :param socket: ``RealtimeSocket`` object describing the currently-
          active realtime session.

        :returns: ``self``, for chainability. """

    if not socket.state is socket.State.ERROR:
      socket.set_state(socket.State.CLOSED)
    handler.on_close(socket.state is not socket.State.ERROR)
    return self

__all__ = (
  'RealtimeSocket',
  'RealtimeSemantics')
