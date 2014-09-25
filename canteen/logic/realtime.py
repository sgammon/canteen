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
from ..util import decorators


# Globals
_ORIGIN_ENV_ITEM = 'HTTP_ORIGIN'
_SOCKET_KEY_ENV_ITEM = 'HTTP_SEC_WEBSOCKET_KEY'
_FORWARDED_FOR_ENV_ITEM = 'HTTP_X_FORWARDED_FOR'


class RealtimeSocket(object):

  """ WIP """

  __slots__ = (
    '__id__',  # ID of the socket
    '__local__',  # local port pair
    '__remote__',  # remote port pair
    '__runtime__',  # link to current runtime
    '__established__')  # establish timestamp

  def __init__(self, runtime,
                     local=None,
                     remote=None):

    """ WIP """

    self.__established__ = time.time()

    self.__id__, self.__runtime__ = (
      hashlib.sha1('::'.join((local, remote))).hexdigest(),
      runtime)

    self.__local__, self.__remote__ = (
      local, remote)

  id, local, remote, runtime, established = (
    property(lambda self: self.__id__),
    property(lambda self: self.__local__),
    property(lambda self: self.__remote__),
    property(lambda self: self.__runtime__),
    property(lambda self: self.__established__))


@decorators.bind('realtime', namespace=True)
class RealtimeSemantics(logic.Logic):

  """ WIP """

  hint = _SOCKET_KEY_ENV_ITEM

  def stream(self, target, send):

    """ WIP """

    def responder(dispatch):

      """ WIP """

      while True:
        inbound = (yield)
        if inbound is not None:
          for outbound in dispatch(inbound):
            send(outbound)

    gen = responder(target)
    gen.next()
    return gen

  def on_connect(self, runtime, request):

    """ WIP """

    # perform handshake through current runtime
    runtime.handshake(*(
      request.environ[self.hint],
      request.environ.get(_ORIGIN_ENV_ITEM, '')))

    # resolve proxies
    return RealtimeSocket(runtime, **{
      'local': request.host,
      'remote': request.remote_addr})


  def on_message(self, runtime, environ, input, output):

    """ WIP """

    responder = self.stream(input, output)

    while True:
      try:
        inbound = runtime.receive()
        if inbound: responder.send(inbound)

      except (GeneratorExit, StopIteration):
        break
    return


__all__ = (
  'RealtimeSocket',
  'RealtimeSemantics')
