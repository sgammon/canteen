# -*- coding: utf-8 -*-

"""

  config utils
  ~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import os
import importlib


## Globals
_appconfig = {}


class Config(object):

  """  """

  __dev__ = None  # debug mode

  seen = set()  # seen config items
  wrap = None  # wrapped config block
  blocks = None  # wrapped config blocks

  ## -- Internals -- ##
  def __init__(self, sub=None, **blocks):

    """  """

    global _appconfig

    self.blocks = blocks or _appconfig
    if not _appconfig:
      _appconfig = blocks
    self.wrap = sub

  ### === Public Attributes === ###

  # block shortcuts
  app = property(lambda self: self.blocks.get('app', {'debug', True}))
  assets = property(lambda self: self.blocks.get('assets', {'debug': True}))
  config = property(lambda self: self.blocks.get('config', {}))

  debug = lambda self: (
    any((self.__dev__,
         os.environ.get('SERVER_SOFTWARE', 'Not Dev').startswith('Dev'),
         os.environ.get('CANTEEN_DEBUG', False) in (
          '1', 'yes', 'on', 'true', 'sure', 'whynot'),
         self.config.get('debug', False),
         self.app.get('debug', False),
         __debug__)))

  app_version = lambda self: (
    '0.0.1-alpha' if 'version' not in self.app else (
      '-'.join(('.'.join(map(str, self.app['version'].values()[:3])),
                             str(self.app['version']['release'])))))

  ### === Public Methods === ###
  load = lambda self, path: (
    self.merge(importlib.import_module(path).config.blocks))
  __get__ = lambda self, instance, owner: self.wrap or self.blocks

  def get(self, key, default=None):

    """  """

    if self.blocks:  # pragma: no cover
      if 'config' in self.blocks:
        return self.blocks['config'].get(key, {'debug': True})
      return self.blocks.get(key, default)
    return default
