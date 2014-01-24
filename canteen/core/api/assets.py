# -*- coding: utf-8 -*-

'''

  canteen: core assets API
  ~~~~~~~~~~~~~~~~~~~~~~~~

  exposes a core API for easily accessing and managing static
  assets attached to a :py:mod:`canteen`-based product.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os
import random
import hashlib
import mimetypes

# core API & util
from . import CoreAPI
from canteen.util import config
from canteen.util import decorators


@decorators.bind('assets')
class AssetsAPI(CoreAPI):

  '''  '''

  __config__ = None  # asset configuration, if any
  __handles__ = {}  # cached file handles for local responders
  __static_types__ = frozenset(('style', 'script', 'font', 'image'))

  ### === Internals === ###
  @property
  def debug(self):

    '''  '''

    return self.config.get('debug', True)

  @property
  def path(self):

    '''  '''

    return config.Config().app.get('paths', {}).get('assets', 'assets')

  @property
  def config(self):

    '''  '''

    return config.Config().assets.get('config', {'debug': True})

  @property
  def assets(self):

    '''  '''

    return config.Config().assets.get('assets', {})

  ### === URL Bindings === ###
  def bind_urls(self, runtime=None):

    '''  '''

    from canteen import url
    from canteen import handler

    ## asset handler
    def make_responder(asset_type):

      '''  '''

      class AssetResponder(handler.Handler):

        '''  '''

        content_types = {
          'css': 'text/css',
          'js': 'application/javascript',
          'svg': 'image/svg+xml',
          'woff': 'font/woff',

        }

        def GET(self, asset):

          '''  '''

          fullpath = os.path.join(self.assets.path, asset_type, asset)
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
              return self.response(status='304 Not Modified', headers=[('ETag', self.request.headers['If-None-Match'])])

          # resolve content type by file extension, if possible
          content_type = self.content_types.get(fullpath.split('.')[-1])
          if not content_type:

            # try to guess with `mimetypes`
            content_type, encoding = mimetypes.guess_type(fullpath)
            if not content_type:
              content_type = 'application/octet-stream'

          return self.response(contents, headers=[('ETag', fingerprint)], content_type=content_type)  # can return content directly

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
              self.abort(404)

            except Exception as e:
              if __debug__: raise
              self.abort(500)

          else:
            return self.abort(404)

      return AssetResponder


    # map asset prefixes to asset responder
    if 'asset_prefix' in self.config:
      for category, prefix in self.config['asset_prefix'].iteritems():
        url("%s-assets" % category, "/%s/<path:asset>" % prefix)(make_responder(category))

  ### === Resolvers === ###
  def find_filepath(self, asset_type):

    '''  '''

    if isinstance(self.path, dict):
      if asset_type in self.path:
        return (self.path['asset_type'], asset_type)
    return (self.path, asset_type)

  def find_path(self, asset_type):

    '''  '''

    asset_prefix = self.config.get('asset_prefix', 'assets')

    if isinstance(asset_prefix, dict):
      # allow type-specific asset prefixes
      if isinstance(asset_prefix, dict):
        if asset_type in asset_prefix:
          return asset_prefix[asset_type]
        raise ValueError("Cannot calculate asset prefix for unspecified asset type '%s'." % asset_type)
    return (asset_prefix, asset_type)

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
      if isinstance(self.config.get('cdn_prefix', None), (list, tuple)):
        cdn_prefix = random.choice(self.config.get('cdn_prefix'))
      else:
        cdn_prefix = self.config.get('cdn_prefix')

      prefix += '//' + cdn_prefix

    return prefix + '/'.join([''] + ['/'.join(map(lambda x: '/'.join(x) if isinstance(x, tuple) else x, url_blocks))])

  @decorators.bind('assets.style_url')  # CSS
  def style_url(self, *fragments, **arguments): return self.asset_url('style', fragments, arguments)

  @decorators.bind('assets.script_url')  # JS
  def script_url(self, *fragments, **arguments): return self.asset_url('script', fragments, arguments)

  @decorators.bind('assets.font_url')  # Fonts
  def font_url(self, *fragments, **arguments): return self.asset_url('font', fragments, arguments)

  @decorators.bind('assets.image_url')  # Images
  def image_url(self, *fragments, **arguments): return self.asset_url('image', fragments, arguments)

  @decorators.bind('assets.static_url')  # Other
  def static_url(self, *fragments, **arguments): return self.asset_url('static', fragments, arguments)


__all__ = ('AssetsAPI',)
