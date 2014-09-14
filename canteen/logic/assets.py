# -*- coding: utf-8 -*-

"""

  assets logic
  ~~~~~~~~~~~~

  exposes logic for managing and making-use-of static assets.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import os
import random
import hashlib
import mimetypes

# core, base & util
from ..base import logic
from ..core import hooks
from ..util import config
from ..util import decorators


## Globals
_default_asset_path = os.path.join(os.getcwd(), 'assets')


@decorators.bind('assets')
class Assets(logic.Logic):

  """ Provides logic related to the use and management of static assets, such as
      images, CSS, JavaScript, fonts, etc.

      Canteen enables two styles of asset management: *registered* and
      *unregistered*. When using registered assets, developers add their static
      files to config (for everything but images) and use a dereferenced naming
      scheme to reference them from templates or handlers. """

  __config__ = None  # asset configuration, if any
  __handles__ = {}  # cached file handles for local responders
  __prefixes__ = {}  # static asset type prefixes
  __static_types__ = frozenset(('style', 'script', 'font', 'image', 'video'))

  ### === Internals === ###
  debug = property(lambda self: self.config.get('debug', True))
  assets = property(lambda self: config.Config().assets.get('assets', {}))

  config = property(lambda self: (
    config.Config().assets.get('config', {'debug': True})))

  path = property(lambda self: (
    config.Config().app.get('paths', {}).get('assets', _default_asset_path)))

  ### === Detection & Bindings === ###
  @hooks.HookResponder('initialize')
  def bind_urls(self):

    """ Bind static asset URLs, if Canteen is instructed to handle requests for
        static assets. Constructs handlers according to URLs and paths from
        application configuration. """

    from canteen import url, handler

    ## asset handler
    def make_responder(asset_type, path_prefix=None):

      """ Internal utility function to make an ``AssetResponder`` handler which
          can handler assets of type ``asset_type`` at prefix ``path_prefix``.

          :param asset_type: Type of asset we're binding this handler for.
          :param path_prefix: URL path prefix that we should respond to.

          :returns: :py:class:`AssetResponder` instance, which is a Canteen
            :py:class:`base.Handler`, preconfigured to handle asset URLs. """


      class AssetResponder(handler.Handler):

        """ Internal :py:class:`canteen.base.Handler` implementation for binding
            to and fulfilling static asset URLs, such as those for CSS, images,
            JavaScript files and SVGs. """

        content_types = {
          'css': 'text/css',
          'js': 'application/javascript',
          'svg': 'image/svg+xml',
          'woff': 'font/woff',
          'png': 'image/png',
          'gif': 'image/gif',
          'jpeg': 'image/jpeg',
          'jpg': 'image/jpeg',
          'webp': 'image/webp',
          'webm': 'video/webm',
          'avi': 'video/avi',
          'mpeg': 'video/mpeg',
          'mp4': 'video/mp4',
          'flv': 'video/x-flv',
          'appcache': 'text/cache-manifest'}

        def GET(self, asset):

          """ Fulfill HTTP GET requests for a particular kind of ``asset_type``
              and ``path_prefix``, which are provided by the outer closure that
              constructs this handler.

              :param asset: Asset to serve. This is a relative path that should
                be translated into a local file and served.

              :returns: Response containing the headers and content to be served
                for the resource specified at ``asset``. """

          fullpath = (
            os.path.join(path_prefix, asset) if path_prefix else (
              os.path.join(self.assets.path, asset_type, asset)))
          if fullpath in self.assets.__handles__:

            # extract cached handle/modtime/content
            modtime, handle, contents, fingerprint = (
              self.assets.__handles__[fullpath])

            if os.path.getmtime(fullpath) > modtime:
              modtime, handle, contents, fingerprint = (
                self.open_and_serve(fullpath))  # need to refresh cache

          else:
            modtime, handle, contents, fingerprint = (
              self.open_and_serve(fullpath))  # need to prime cache

          # try to serve a 304, if possible
          if 'If-None-Match' in self.request.headers:

            # fingerprint matches, serve a 304
            if self.request.headers['If-None-Match'] == fingerprint:
              etag_header = ('ETag', self.request.headers['If-None-Match'])
              return self.http.new_response(
                        status='304 Not Modified',
                        headers=[etag_header])

          # resolve content type by file extension, if possible
          content_type = self.content_types.get(fullpath.split('.')[-1])
          if not content_type:

            # try to guess with `mimetypes`
            content_type, encoding = mimetypes.guess_type(fullpath)
            if not content_type: content_type = 'application/octet-stream'

          # can return content directly
          return self.http.new_response(contents,
                                        headers=[('ETag', fingerprint)],
                                        content_type=content_type)

        # noinspection PyBroadException
        def open_and_serve(self, filepath):

          """ Utility function to open a static asset file and serve its
              contents. Takes a filepath and properly handles MIME/content-type
              negotiation before responding with the asset.

              :param filepath: Path to the static asset to be served.

              :returns: Structure (``tuple``) containing:
                - a timestamp for when the asset was last modified, provided by
                  ``getmtime`` from the OS
                - original handle to the file, which should be closed after
                  exiting this function
                - the contents of the file, as a string
                - an MD5 hash of the contents of the file, as a hex digest """

          if os.path.exists(filepath):
            try:
              with open(filepath, 'rb') as fhandle:

                # assign to cache location by file path
                contents = fhandle.read()
                self.assets.__handles__[filepath] = (
                  os.path.getmtime(filepath),
                  fhandle,
                  contents,
                  hashlib.md5(contents).hexdigest())
                return self.assets.__handles__[filepath]

            except IOError:
              if __debug__: raise
              self.error(404)

            except Exception:
              if __debug__: raise
              self.error(500)

          else:
            return self.error(404)

      return AssetResponder

    # set default asset prefixes
    asset_prefixes = self.__prefixes__ = {
      'style': 'assets/style',
      'image': 'assets/img',
      'script': 'assets/script',
      'font': 'assets/font',
      'video': 'assets/video',
      'other': 'assets/ext'
    } if 'asset_prefix' not in self.config else self.config['asset_prefix']

    for category, prefix in asset_prefixes.iteritems():
      url("%s-assets" % category, "/%s/<path:asset>" % prefix)((
        make_responder(asset_type=category)))

    if 'extra_assets' in self.config:
      for name, ext_cfg in self.config['extra_assets'].iteritems():
        prefix, path = ext_cfg
        url("%s-extra-assets" % name, "%s/<path:asset>" % prefix)((
          make_responder(asset_type=name, path_prefix=path)))

  ### === Resolvers === ###
  def find_filepath(self, asset_type):

    """  """

    if isinstance(self.path, dict):
      if asset_type in self.path:
        return (self.path['asset_type'], asset_type)
    return (self.path, asset_type)

  def find_path(self, asset_type):

    """  """

    if isinstance(self.__prefixes__, dict):
      # allow type-specific asset prefixes
      if asset_type in self.__prefixes__:
        return self.__prefixes__[asset_type]
      raise ValueError("Cannot calculate asset prefix"
                       " for unspecified asset type '%s'." % asset_type)
    return ("assets/%s" % asset_type, asset_type)

  ### === URL Builders === ###
  def asset_url(self, type, fragments, arguments):

    """  """

    assert (fragments or arguments)  # must pass at least fragments or arguments

    if type not in self.__static_types__:
      raise ValueError("Cannot generate asset URL"
                       " for unknown asset type '%s'." % type)

    if fragments:
      url_blocks = {

        # one fragment will be a relative URL, like "sample/app.css?v1"
        1: lambda relative: (self.find_path(type), relative),

        # two fragments is a package + name
        2: lambda package, name: self.find_name(type, package, name),

        # three fragments is a package + name + version
        3: lambda name, package, version: self.find_name(*(
          type, package, name), version=version)

      }.get(len(fragments))(*fragments)

    if arguments:
      # @TODO(sgammon): make this named-parameter friendly
      raise RuntimeError('Keyword-based asset URLs are not yet supported.')

    # build relative URL unless specified otherwise
    if arguments.get('absolute'):
      pass

    # should we use a CDN prefix?
    prefix = ''
    if self.config.get('serving_mode', 'local') == 'cdn':
      prefix += random.choice(self.config.get('cdn_prefix')) if (
        isinstance(self.config.get('cdn_prefix', None), (list, tuple))) else (
          self.config.get('cdn_prefix'))

    return prefix + '/'.join([''] + ['/'.join(map(lambda x: '/'.join(x) if (
      isinstance(x, tuple)) else x, url_blocks))])

  @decorators.bind()  # CSS
  def style_url(self, *fragments, **arguments):

    """ Exports logic to calculate a URL for a *regsitered* or *unregistered*
        static CSS asset from a set of spec ``fragments`` and ``arguments``.

      :param fragments: Positional specification fragments that should be used
        to resolve the asset to be linked-to.

      :param arguments: Keyword arguments to be used for filling in path items
        when building the CSS asset URL.

      :return: Generated CSS asset URL. """

    return (
    self.asset_url('style', fragments, arguments))

  @decorators.bind()  # JS
  def script_url(self, *fragments, **arguments): return (
    self.asset_url('script', fragments, arguments))

  @decorators.bind()  # Fonts
  def font_url(self, *fragments, **arguments): return (
    self.asset_url('font', fragments, arguments))

  @decorators.bind()  # Images
  def image_url(self, *fragments, **arguments): return (
    self.asset_url('image', fragments, arguments))

  @decorators.bind()  # Video
  def video_url(self, *fragments, **arguments): return (
    self.asset_url('video', fragments, arguments))

  @decorators.bind()  # Other
  def static_url(self, *fragments, **arguments): return (
    self.asset_url('static', fragments, arguments))
