# -*- coding: utf-8 -*-

'''

  canteen: config utils
  ~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os
import importlib
import collections


## Globals
_appconfig = {}


class Config(object):

  '''  '''

  seen = set()  # seen config items
  wrap = None  # wrapped config block
  blocks = None  # wrapped config blocks

  ## -- Internals -- ##
  def __init__(self, sub=None, **blocks):

    '''  '''

    global _appconfig

    self.blocks = blocks or _appconfig
    if not _appconfig:
      _appconfig = blocks
    if sub:
      self.wrap = sub

  ### === Public Attributes === ###
  @property
  def debug(self):

    '''  '''

    return any((
      os.environ.get('SERVER_SOFTWARE', 'Not Dev').startswith('Dev'),
      os.environ.get('CANTEEN_DEBUG', None) in ('1', 'yes', 'on', 'true', 'sure'),
      self.config.get('debug', False),
      self.app.get('debug', False),
      __debug__
    ))

  @property
  def app(self):

    '''  '''

    return self.blocks.get('app', {'debug': True})

  @property
  def assets(self):

    '''  '''

    return self.blocks.get('assets', {'debug': True})

  @property
  def config(self):

    '''  '''

    return self.blocks.get('config', {})

  @property
  def app_version(self):

    '''  '''

    if 'version' in self.app:
      return '-'.join(('.'.join(map(str, self.app['version'].values()[:3])), str(self.app['version']['release'])))
    return '0.0.1-alpha'

  ### === Public Methods === ###
  def load(self, path):

    '''  '''

    module = importlib.import_module(path)
    self.merge(module.config.blocks)

  def get(self, key, default=None):

    '''  '''

    if self.blocks:
      if 'config' in self.blocks:
        return self.blocks['config'].get(key, {'debug': True})
      return self.blocks.get(key, default)
    return default

  def __get__(self, instance, owner):

    '''  '''

    return self.wrap or self.blocks


__all__ = ('Config',)
