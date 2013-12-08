# -*- coding: utf-8 -*-

'''

  canteen config utils
  ~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import os
import importlib
import collections


## Globals
_appconfig = None


class Config(object):

  '''  '''

  seen = set()  # seen config items
  wrap = None  # wrapped config block
  blocks = None  # wrapped config blocks

  ## -- Internals -- ##
  def __new__(self, sub=None, **blocks):

    '''  '''

    global _appconfig

    if not sub:
      if not _appconfig:
        _appconfig = super(Config, self).__new__(Config)
        _appconfig.__init__(**blocks)
      return _appconfig

    wrapper = super(Config, self).__new__(Config)
    wrapper.__init__(sub)
    return wrapper

  def __init__(self, sub=None, **blocks):

    '''  '''

    self.blocks = blocks
    if sub:
      self.wrap = sub

  ### === Public Attributes === ###
  @property
  def debug(self):

    '''  '''

    return any((
      os.environ.get('SERVER_SOFTWARE').startswith('Dev'),
      os.environ.get('CANTEEN_DEBUG', None) in ('1', 'yes', 'on', 'true', 'sure'),
      __debug__
    ))

  @property
  def app(self):

    '''  '''

    return self.blocks.get('app', {})

  @property
  def config(self):

    '''  '''

    return self.__class__(self.blocks.get('config', {}))

  ### === Public Methods === ###
  def load(self, path):

    '''  '''

    module = importlib.import_module(path)
    self.merge(module.config.blocks)

  def get(self, key, default=None):

    '''  '''

    if 'config' in self.blocks:
      return self.blocks['config'].get(key, {'debug': True})
    return self.blocks.get(key, default)
