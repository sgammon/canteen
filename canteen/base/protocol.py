# -*- coding: utf-8 -*-

'''

  protocol base
  ~~~~~~~~~~~~~

  ``Protocol`` classes help the framework understand different serialization
  dialects for use in RPC. For example, the JSON format used for most browser
  is specified as a ``Protocol``.

  As is customary with :py:mod:`protorpc` (where the equivalent class used to
  be called a ``Mapper`` and is now just a sloppy collection of ``object``s),
  ``Protocol``s register ``Content-Type``s to respond to. When an RPC message
  matching that content type is submitted, the proper ``Protocol`` is used to
  decode it.

  On the client side, ``Protocol`` objects can be used by handing in a custom
  object when creating a ``Transport``.

  Example:

    # -*- coding: utf-8 -*-
    import json
    from canteen import Protocol

    @Protocol.register('jsonrpc', ('application/json', 'text/json'))
    class JSONRPC(Protocol):

      """ I implement JSONRPC """

      def encode_message(self, message):

        """ Use builtin model JSON to serialize """

        return message.to_json()

      def decode_message(self, message_type, encoded_message):

        """ Blindly decode like a boss """

        return message_type(**json.loads(encoded_message))


  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import abc

# canteen util & core
from ..core import runtime
from ..util import decorators


with runtime.Library('protorpc') as (library, protorpc):

  # protorpc
  messages, protojson, remote = library.load(*(
    'messages',
    'protojson',
    'remote'
  ))


  @decorators.configured
  class Protocol(object):

    ''' Base ``Protocol`` class for adding serialization dialects to the RPC
        engine. Implementing subclasses is easy - just specify an encoder and
        decoder function at ``encode_message`` and ``decode_message``.

        Once a ``Protocol`` class is written, it can be registered with the RPC
        subsystem by decorating it with ``Protocol.register``, along with a
        short string name (for instance, ``jsonrpc``) and a set of content types
        to respond to. '''

    __label__ = None  # string (human) name for the protocol
    __config__ = None  # local configuration info
    __protocols__ = {}  # class-level map of all protocols to their names
    __metaclass__ = abc.ABCMeta  # enforce ABC compliance
    __content_types__ = ('',)  # default to no matched content types

    ## == Multi-protocol Tools == ##
    @decorators.classproperty
    def all(cls):

      ''' Class-level generator accessor to iterate through all registered
          ``Protocol`` implementations. Used at construction time to find
          protocol classes to bundle into a :py:mod:`protorpc` ``Protocols``
          object.

          :returns: Yields ``Protocol`` implementations one at a time. '''

      for protocol in cls.__protocols__.itervalues():
        yield protocol

    @decorators.classproperty
    def mapping(cls):

      ''' Class-level accessor for creating a :py:mod:`protorpc` ``Protocols``
          container, which resolves the proper ``Protocol`` object to dispatch
          an RPC with, based on the HTTP ``Content-Type`` header.

          :returns: :py:class:`protorpc.remote.Protocols` object containing all
                    registered :py:class:`Protocol` objects. '''

      # construct a protocol container
      container = remote.Protocols()

      for protocol in cls.all:

        # construct protocol singleton and add to container
        singleton = protocol()

        container.add_protocol(*(
          singleton,
          singleton.name,
          singleton.content_type,
          singleton.alternative_content_types
        ))

      return container

    ## == Registration Decorator == ##
    @classmethod
    def register(cls, name, types, **config):

      ''' Register a ``Protocol`` implementation by name and a set of content
          types. Usually used as a decorator.

          Args:
            :param name:
            :type  name:

            :param types:
            :type  types:

          Kwargs:

          :returns: '''

      assert isinstance(name, basestring), "protocol name must be a string"
      assert isinstance(types, (list, tuple)), "types must be an iterable"

      def _register_protocol(klass):

        ''' Closure to register a class as an available protocol right before
            class construction. Mounts a ``Protocol``'s label, content types,
            and configuration.

            :param klass:
            :type  klass:

            :returns: '''

        # assign protocol details
        klass.__label__, klass.__content_types__, klass.__config__ = (
          name,
          types,
          config
        )

        if name not in Protocol.__protocols__:
          Protocol.__protocols__[name] = klass  # register :)

        return klass

      return _register_protocol

    ## == Protocol Properties == ##
    @decorators.classproperty
    def name(self):

      ''' Class-level accessor for the 'short name' of this ``Protocol`` class.
          For example, ``jsonrpc``.

          :returns: ``str`` short name for this :py:class:`Protocol`. '''

      return self.__label__

    @decorators.classproperty
    def content_type(self):

      ''' Class-level accessor for the primary ``Content-Type`` this
          :py:class:`Protocol` should respond to. The first entry in the
          available options is used as the primary ``Content-Type``.

          :returns: Primary ``str`` ``Content-Type`` value. '''

      return self.__content_types__[0]

    @decorators.classproperty
    def alternative_content_types(self):

      ''' Class-level accessor for 'alternative' ``Content-Type``s that this
          :py:class:`Protocol` should respond to. Alternative content types
          will be responded to, but not used for responses (the 'primary'
          ``Content-Type`` is used as the response's type).

          :returns: ``list`` of ``str`` ``Content-Type``s. '''

      return [i for i in (
        filter(lambda x: x != self.content_type, self.__content_types__))]

    ## == Abstract Methods == ##
    @abc.abstractmethod
    def encode_message(self, message):  # pragma: no cover

      ''' Encode a message according to this :py:class:`Protocol`. Must be
          implemented by child classes, and so is marked as an abstract method.

          Failure to specify this method will prevent an implementing class
          from being constructed.

          Args:
            :param message:
            :type  message:

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: ``None``, but child class implementations are expected
                    to return an encoded ``str``/``unicode`` representation
                    of ``message``. '''

      raise NotImplementedError('Method `Protocol.encode_message` is abstract.')

    @abc.abstractmethod
    def decode_message(self, message_type, encoded_message):  # pragma: no cover

      ''' Decode a message according to this :py:class:`Protocol`. Must be
          implemented by child classes, and so is marked as an abstract method.

          Failure to specify this method will prevent an implementing class
          from being constructed.

          Args:
            :param message_type:
            :type  message_type:

            :param encoded_message:
            :type  encoded_message:

          :raises NotImplementedError: Always, as this method is abstract.

          :returns: ``None``, but child class implementations are expected
                    to return an inflated ``message_type`` based on the
                    provided ``encoded_message``. '''

      raise NotImplementedError('Method `Protocol.decode_message` is abstract.')

    CONTENT_TYPE = content_type
    ALTERNATIVE_CONTENT_TYPES = alternative_content_types


  __all__ = ('Protocol',)
