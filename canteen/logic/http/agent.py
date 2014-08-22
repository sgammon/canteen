# -*- coding: utf-8 -*-

'''

  HTTP agent logic
  ~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# canteen core & util
from canteen.base import logic
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

  def dump(self):

    '''  '''

    return dict(((k, getattr(self, k, None)) for k in self.__slots__))

  def __repr__(self):

    '''  '''

    return "%s(%s)" % (
      self.__class__.__name__.replace('Agent', ''),
      ', '.join(
        ('='.join((
          i,
          str(getattr(self, i) if (hasattr(self, i)) else None))) for i in self.__slots__ if not i.startswith('__'))
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
  def scan(cls, request, user_agent, detected):

    '''  '''

    return cls(*{
        'bsd': ('BSD', Vendor.OPEN, AgentVersion(0)),
        'linux': ('Linux', Vendor.OPEN, AgentVersion(0)),
        'macos': ('Mac OS X', Vendor.APPLE, AgentVersion(0)),
        'windows': ('Windows', Vendor.MICROSOFT, AgentVersion(0)),
        'ipad': ('iOS', Vendor.APPLE, AgentVersion(0)),
        'iphone': ('iOS', Vendor.APPLE, AgentVersion(0))
    }.get(user_agent.platform.lower().strip(), ('unknown', Vendor.OTHER, AgentVersion(0))))


class AgentCapabilities(AgentInfo):

  '''  '''

  __slots__ = (
    'spdy',  # support for SPDY
    'quic',  # support for QUIC
    'webp',  # support for WebP
    'webm',  # support for WebM
  )

  def __init__(self, **kwargs):

    '''  '''

    for datapoint in self.__slots__:
      setattr(self, datapoint, kwargs[datapoint] if datapoint in kwargs else None)

  @classmethod
  def scan(cls, request, user_agent, detected):

    '''  '''

    detected = {}  # detected capabilities
    accept_string = request.headers['Accept'] if 'Accept' in request.headers else ''

    for datapoint, conditional in ((

      ('quic', user_agent.browser == 'chrome'),
      ('spdy', user_agent.browser in ('chrome', 'firefox', 'opera')),
      ('webm', user_agent.browser in ('chrome', 'firefox', 'opera')),
      ('webp', user_agent.browser == 'chrome' or 'webp' in accept_string),

      )):

      detected[datapoint] = conditional

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

    # == Accept Header == #
    'charsets',  # accepted charsets
    'encodings',  # accepted encodings
    'languages',  # accepted languages
    'mimetypes',  # accepted mimetypes

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
    'googlebot',  # is this google's crawler?
    'aol',  # is this AOL's crawler?
    'ask',  # is this Ask's crawler?
    'yahoo',  # is this Yahoo's crawler?

    # == Environment == #
    'mobile',  # can we detect that this is a mobile device? (always truthy for tablets too)
    'tablet',  # can we detect that this is a tablet?
    'desktop',  # or do we fallback to desktop?
    'crawler',  # is this a known crawler?

    # == Engines == #
    'gecko',  # old mozilla/netscape engine
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
  def scan(cls, request, ua):

    '''  '''

    detected = {}  # holds detected truths/guesses

    # copy over raw strings
    detected['accept'] = request.headers.get('accept')
    detected['string'] = request.headers.get('user-agent')

    # copy over accept details
    detected['charsets'], detected['encodings'], detected['languages'], detected['mimetypes'] = (
      request.accept_charsets, request.accept_encodings, request.accept_languages, request.accept_mimetypes
    )

    # detect version first
    version = detected['version'] = ua.version.split('.')
    version_spec = []

    # take each version section as major, minor, micro
    for grouping in version:
      if len(version_spec) >= 3:
        break
      try:
        version_spec.append(int(grouping))
      except:
        break

    # if we detected *anything* as an int, add it as our version
    version = detected['version'] = AgentVersion(*tuple(version_spec)) if version_spec else AgentVersion(0)
    platform = ua.platform.lower().strip()


    # all others
    for datapoint, condition in ((

      ## Browser
      ('chrome', ua.browser == 'chrome'),
      ('firefox', ua.browser == 'firefox'),
      ('seamonkey', ua.browser == 'seamonkey'),
      ('safari', ua.browser == 'safari'),
      ('opera', ua.browser == 'opera'),
      ('msie', ua.browser == 'msie'),
      ('googlebot', ua.browser == 'google'),
      ('yahoo', ua.browser == 'yahoo'),
      ('aol', ua.browser == 'aol'),
      ('ask', ua.browser == 'ask'),

      ## Engines
      ('trident', ua.browser == 'msie'),
      ('blink', ua.browser in ('chrome', 'opera')),
      ('presto', ua.browser == 'opera' and version.major < 15),  # @TODO(sgammon): version specificity
      ('webkit', ua.browser in ('safari', 'chrome', 'opera')),
      ('spidermonkey', ua.browser in ('firefox', 'seamonkey')),
      ('gecko', 'Gecko' in ua.string and ('WebKit' not in ua.string and 'Chrome' not in ua.string)),

      ## Environments
      ('tablet', 'Tabl' in ua.string or 'iPad' in ua.string),
      ('crawler', ua.browser in ('google', 'yahoo', 'aol', 'ask')),
      ('mobile', 'Mobi' in ua.string or 'IEMobile' in ua.string or platform in ('ios', 'iphone', 'ipad'))

      )):
      detected[datapoint] = condition

    # detect vendor
    detected['vendor'] = Vendor.OTHER
    for k, v in {
        Vendor.GOOGLE: detected.get('chrome') or detected.get('googlebot'),
        Vendor.MOZILLA: detected.get('firefox') or detected.get('seamonkey'),
        Vendor.MICROSOFT: detected.get('msie'),
        Vendor.OPERA: detected.get('opera'),
        Vendor.APPLE: detected.get('safari'),
        Vendor.OPEN: detected.get('seamonkey'),
      }.iteritems():

      if v: detected['vendor'] = k

    # desktop mode
    detected['desktop'] = not any((detected.get('mobile'), detected.get('tablet')))

    # OS detection
    detected['__os__'] = AgentOS.scan(request, ua, detected)

    # capabilities detection
    detected['__supports__'] = AgentCapabilities.scan(request, ua, detected)

    # judge modern/ancient
    detected['modern'] = (detected['chrome'] or detected['safari'] or detected['firefox'] or detected['opera']) and (
      detected['__os__'].name in ('Mac OS X', 'Windows', 'Linux')
    )

    # calculate quality preferences
    detected['quality'] = {}
    if 'mimetypes' in detected:
      for mime, quality in detected['mimetypes']:
        detected['quality'][mime] = quality

    detected['ancient'] = not detected['modern']
    return cls(**detected)


@decorators.bind('http.agent')
class UserAgent(logic.Logic):

  '''  '''

  def scan(self, request):

    '''  '''

    return AgentFingerprint.scan(request, request.user_agent)


__all__ = (
  'AgentAPI',
  'AgentVendor',
  'AgentOS',
  'AgentFingerprint',
  'AgentCapabilities'
)
