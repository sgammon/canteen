# -*- coding: utf-8 -*-

'''

  canteen: protocol base
  ~~~~~~~~~~~~~~~~~~~~~~

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


  class Protocol(object):

    '''  '''

    __label__ = None  # string (human) name for the protocol
    __config__ = None  # local configuration info
    __protocols__ = {}  # class-level map of all protocols to their names
    __metaclass__ = abc.ABCMeta  # enforce ABC compliance
    __content_types__ = ('',)  # default to no matched content types

    ## == Multi-protocol Tools == ##
    @decorators.classproperty
    def all(cls):

      '''  '''

      for protocol in cls.__protocols__.itervalues():
        yield protocol

    @decorators.classproperty
    def mapping(cls):

      '''  '''

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
    def register(cls, name, content_types, **config):

      '''  '''

      assert isinstance(name, basestring), "protocol name must be a string"
      assert isinstance(content_types, (list, tuple)), "content_types must be an iterable"

      def _register_protocol(klass):

        '''  '''

        # assign protocol details
        klass.__label__, klass.__content_types__, klass.__config__ = (
          name,
          content_types,
          config
        )

        Protocol.__protocols__[name] = klass  # register :)

        return klass

      return _register_protocol

    ## == Protocol Properties == ##
    @decorators.classproperty
    def name(self):

      '''  '''

      return self.__label__

    @decorators.classproperty
    def content_type(self):

      '''  '''

      return self.__content_types__[0]

    @decorators.classproperty
    def alternative_content_types(self):

      '''  '''

      return [i for i in filter(lambda x: x != self.content_type, self.__content_types__)]

    ## == Abstract Methods == ##
    @abc.abstractmethod
    def encode_message(self, message):

      '''  '''

      raise NotImplementedError('Method `Protocol.encode_message` is abstract.')

    @abc.abstractmethod
    def decode_message(self, message_type, encoded_message):

      '''  '''

      raise NotImplementedError('Method `Protocol.decode_message` is abstract.')

    CONTENT_TYPE = content_type
    ALTERNATIVE_CONTENT_TYPES = alternative_content_types


  __all__ = ('Protocol',)
