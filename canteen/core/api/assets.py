# -*- coding: utf-8 -*-

'''

  canteen: core assets API
  ~~~~~~~~~~~~~~~~~~~~~~~~

  exposes a core API for easily accessing and managing static
  assets attached to a :py:mod:`canteen`-based product.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os
import random
import hashlib
import mimetypes

# core API & util
from . import CoreAPI, hooks
from canteen.util import config
from canteen.util import decorators


## Globals
_default_asset_path = os.path.join(os.getcwd(), 'assets')


@decorators.bind('assets')
class AssetsAPI(CoreAPI):

  '''  '''

  __config__ = None  # asset configuration, if any
  __handles__ = {}  # cached file handles for local responders
  __prefixes__ = {}  # static asset type prefixes
  __static_types__ = frozenset(('style', 'script', 'font', 'image', 'video'))

  ### === Internals === ###
  debug = property(lambda self: self.config.get('debug', True))
  assets = property(lambda self: config.Config().assets.get('assets', {}))
  config = property(lambda self: config.Config().assets.get('config', {'debug': True}))
  path = property(lambda self: config.Config().app.get('paths', {}).get('assets', _default_asset_path))

  ### === Detection & Bindings === ###
  @hooks.HookResponder('initialize', context=('runtime',))
  def bind_urls(self, runtime):

    '''  '''

    from canteen import url, handler

    ## asset handler
    def make_responder(asset_type, path_prefix=None):

      '''  '''

      class AssetResponder(handler.Handler):

        '''  '''

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
          'appcache': 'text/cache-manifest'
        }

        def GET(self, asset):

          '''  '''

          fullpath = os.path.join(path_prefix, asset) if path_prefix else os.path.join(self.assets.path, asset_type, asset)
          if fullpath in self.assets.__handles__:

            # extract cached handle/modtime/content
            modtime, handle, contents, fingerprint = self.assets.__handles__[fullpath]

            if os.path.getmtime(fullpath) > modtime:
              modtime, handle, contents, fingerprint = self.open_and_serve(fullpath)  # need to refresh cache

          else:
            modtime, handle, contents, fingerprint = self.open_and_serve(fullpath)  # need to prime cache in first place

          # try to serve a 304, if possible
          if 'If-None-Match' in self.request.headers:
            if self.request.headers['If-None-Match'] == fingerprint:  # fingerprint matches, serve a 304
              return self.http.new_response(status='304 Not Modified', headers=[('ETag', self.request.headers['If-None-Match'])])

          # resolve content type by file extension, if possible
          content_type = self.content_types.get(fullpath.split('.')[-1])
          if not content_type:

            # try to guess with `mimetypes`
            content_type, encoding = mimetypes.guess_type(fullpath)
            if not content_type: content_type = 'application/octet-stream'

          return self.http.new_response(contents, headers=[('ETag', fingerprint)], content_type=content_type)  # can return content directly

        def open_and_serve(self, filepath):

          '''  '''

          if os.path.exists(filepath):
            try:
              with open(filepath, 'rb') as fhandle:

                # assign to cache location by file path
                contents = fhandle.read()
                self.assets.__handles__[filepath] = (os.path.getmtime(filepath), fhandle, contents, hashlib.md5(contents).hexdigest())
                return self.assets.__handles__[filepath]

            except IOError as e:
              if __debug__: raise
              self.error(404)

            except Exception as e:
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
      url("%s-assets" % category, "/%s/<path:asset>" % prefix)(make_responder(asset_type=category))

    if 'extra_assets' in self.config:
      for name, ext_cfg in self.config['extra_assets'].iteritems():
        prefix, path = ext_cfg
        url("%s-extra-assets" % name, "%s/<path:asset>" % prefix)(make_responder(asset_type=name, path_prefix=path))

  ### === Resolvers === ###
  def find_filepath(self, asset_type):

    '''  '''

    if isinstance(self.path, dict):
      if asset_type in self.path:
        return (self.path['asset_type'], asset_type)
    return (self.path, asset_type)

  def find_path(self, asset_type):

    '''  '''

    if isinstance(self.__prefixes__, dict):
      # allow type-specific asset prefixes
      if asset_type in self.__prefixes__:
        return self.__prefixes__[asset_type]
      raise ValueError("Cannot calculate asset prefix for unspecified asset type '%s'." % asset_type)
    return ("assets/%s" % asset_type, asset_type)

  def find_prefix(self, asset_type, package):

    '''  '''

    import pdb; pdb.set_trace()

  def find_name(self, asset_type, package, name, version=None):

    '''  '''

    pass

  ### === URL Builders === ###
  def asset_url(self, type, fragments, arguments):

    '''  '''

    assert (fragments or arguments)  # must pass at least fragments or arguments

    if type not in self.__static_types__:
      raise ValueError("Cannot generate asset URL for unknown asset type '%s'." % type)

    if fragments:
      url_blocks = {

        # one fragment will be a relative URL, like "sample/app.css?v1"
        1: lambda relative: (self.find_path(type), relative),

        # two fragments is a package + name, like ("sample", "app")
        2: lambda package, name: self.find_name(type, package, name),

        # three fragments is a package + name + version, like ("sample", "app", "v1")
        3: lambda name, package, version: self.find_name(type, package, name, version=version)

      }.get(len(fragments))(*fragments)

    if arguments:
      raise RuntimeError('Keyword-based asset URLs are not yet supported.')  # @TODO(sgammon): make this named-parameter friendly

    # build relative URL unless specified otherwise
    if arguments.get('absolute'):
      pass

    # should we use a CDN prefix?
    prefix = ''
    if self.config.get('serving_mode', 'local') == 'cdn':
      prefix += random.choice(self.config.get('cdn_prefix')) if (
        isinstance(self.config.get('cdn_prefix', None), (list, tuple))) else self.config.get('cdn_prefix')

    return prefix + '/'.join([''] + ['/'.join(map(lambda x: '/'.join(x) if isinstance(x, tuple) else x, url_blocks))])

  @decorators.bind()  # CSS
  def style_url(self, *fragments, **arguments): return self.asset_url('style', fragments, arguments)

  @decorators.bind()  # JS
  def script_url(self, *fragments, **arguments): return self.asset_url('script', fragments, arguments)

  @decorators.bind()  # Fonts
  def font_url(self, *fragments, **arguments): return self.asset_url('font', fragments, arguments)

  @decorators.bind()  # Images
  def image_url(self, *fragments, **arguments): return self.asset_url('image', fragments, arguments)

  @decorators.bind()  # Video
  def video_url(self, *fragments, **arguments): return self.asset_url('video', fragments, arguments)

  @decorators.bind()  # Other
  def static_url(self, *fragments, **arguments): return self.asset_url('static', fragments, arguments)


__all__ = ('AssetsAPI',)
