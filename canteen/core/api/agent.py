# -*- coding: utf-8 -*-

'''

  canteen core agent API
  ~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# canteen core & util
from . import content
from . import CoreAPI
from canteen.util import struct
from canteen.util import decorators


class Vendor(struct.BidirectionalEnum):

  '''  '''

  GOOGLE = 0  # Chrome
  MOZILLA = 1  # Firefox
  MICROSOFT = 2  # IE
  OPERA = 3  # Opera
  APPLE = 4  # Apple
  OPEN = 5  # Open source
  OTHER = 6  # Anything else


class AgentInfo(object):

  '''  '''

  __slots__ = tuple()

  def __repr__(self):

    '''  '''

    return "%s(%s)" % (
      self.__class__.__name__.replace('Agent', ''),
      ', '.join(
        ('='.join((i, str(getattr(self, i) if (hasattr(self, i)) else None))) for i in self.__slots__ if not i.startswith('__'))
      )
    )


class AgentVersion(AgentInfo):

  '''  '''

  __slots__ = (
    'major',  # major browser version (the `3` in 3.0)
    'minor',  # minor browser version (the `1` in 3.1)
    'micro'  # micro browser version (the `5` in 3.1.5)
  )

  def __init__(self, major, minor=None, micro=None):

    '''  '''

    self.major, self.minor, self.micro = major, minor, micro


class AgentOS(AgentInfo):

  '''  '''

  __slots__ = (
    'name',  # `Mac OS X` for mac, `Windows XP` for Windows, etc
    'vendor',  # vendor of the OS, from above
    'version'  # detected version of the OS
  )

  def __init__(self, name, vendor, version):

    '''  '''

    self.name, self.vendor, self.version = name, vendor, version

  @classmethod
  def scan(self, fingerprint):

    '''  '''

    return cls(name=None, vendor=None, version=None)


class AgentCapabilities(AgentInfo):

  '''  '''

  __slots__ = (
    'spdy',  # support for SPDY
    'quic',  # support for QUIC
    'webp',  # support for WebP
    'webm',  # support for WebM
    'http2',  # support for HTTP2
    'retina',  # support for double-DPI
    'websocket'  # support for websockets
  )

  def __init__(self, **kwargs):

    '''  '''

    for datapoint in self.__slots__:
      setattr(self, datapoint, kwargs[datapoint] if datapoint in kwargs else None)

  @classmethod
  def scan(cls, fingerprint):

    '''  '''

    detected = {}
    return cls(**detected)


class AgentFingerprint(AgentInfo):

  '''  '''

  __slots__ = (

    # == Basic Data == #
    'accept',  # full Accept request header
    'string',  # full User-Agent request header
    'vendor',  # detected Vendor of this browser (enumerated in AgentVendor)
    'version',  # detected version of this browser
    'quality',  # global relative quality preference

    # == General Flags == #
    'modern',  # is this browser generally considered `modern`?
    'ancient',  # or is this browser considered `ancient`?

    # == Specific Browsers == #
    'chrome',  # is this Chrome or Chromium?
    'seamonkey',  # is this Seamonkey?
    'msie',  # is this Internet Exporer?
    'safari',  # is this Safari?
    'firefox',  # is this Firefox?
    'opera',  # is this Opera?

    # == Environment == #
    'mobile',  # can we detect that this is a mobile device? (always truthy for tablets too)
    'tablet',  # can we detect that this is a tablet?
    'desktop',  # or do we fallback to desktop?

    # == Engines == #
    'blink',  # is this the `blink` fork of webkit (Chrome)?
    'webkit',  # is this webkit (Chrome/Safari)?
    'presto',  # is this an early Opera engine, pre-Blink?
    'trident',  # always active during MSIE requests
    'spidermonkey',  # is this spidermonkey (mozilla)?

    # == Internals == #
    '__os__',  # holds an `AgentOS` object
    '__supports__'  # holds an `AgentCapabilities` object

  )

  def __init__(self, **kwargs):

    '''  '''

    for datapoint in self.__slots__:
      setattr(self, datapoint, kwargs[datapoint] if datapoint in kwargs else None)

  @property
  def os(self):

    '''  '''

    if not hasattr(self, '__os__') or (hasattr(self, '__os__') and not self.__os__):
      self.__os__ = AgentOS.scan(self)
    return self.__os__

  @property
  def supports(self):

    '''  '''

    if not hasattr(self, '__supports__') or (hasattr(self, '__supports__') and not self.__supports__):
      self.__supports__ = AgentCapabilities.scan(self)
    return self.__supports__

  capabilities = supports

  @classmethod
  def scan(cls, handler, environ, request):

    '''  '''

    detected = {}
    return cls(**detected)


@decorators.bind('user_agent')
class AgentAPI(CoreAPI):

  '''  '''

  @content.ContentFilter(handler=True)
  def scan(self, handler, environ, start_response, endpoint, arguments, request, http):

    '''  '''

    from canteen.base import handler as base_handler

    if isinstance(handler, base_handler.Handler):
      # it's a canteen handler class - we can safely attach agent detection
      handler.set_agent(AgentFingerprint.scan(handler, environ, request))


__all__ = (
  'AgentAPI',
  'AgentVendor',
  'AgentOS',
  'AgentFingerprint',
  'AgentCapabilities'
)
