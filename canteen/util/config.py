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
  blocks = {}  # configuration blocks

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

    for k in blocks:
      if not k in self.blocks:
        self.blocks[k] = blocks[k]
      else:
        self.merge(blocks[k], self.blocks[k])
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

    return self.__class__(self.blocks.get('app', {}))

  @property
  def config(self):

    '''  '''

    return self.__class__(self.blocks.get('config', {}))

  ### === Public Methods === ###
  def merge(self, blocks, base):

    '''  '''

    merged = {}
    for k, v in blocks.iteritems():
      self.seen.add(k)
      if isinstance(v, collections.Mapping):
        if k in base:
          merged[k] = self.merge(blocks[k], base[k])
          continue
        merged[k] = v

    self.blocks.update(merged)
    return self.blocks

  def load(self, path):

    '''  '''

    module = importlib.import_module(path)
    self.merge(module.config.blocks)

  def get(self, key, default=None):

    '''  '''

    for block in self.blocks:
      if key in self.blocks[block]:
        return self.blocks[block][key]
    return {'debug': True}

  ### === Item Protocol === ###
  def __getitem__(self, key):

    '''  '''

    pass

  def __setitem__(self, key, value):

    '''  '''

    pass

  ### === Attribute Protocol === ###
  def __getattr__(self, key):

    '''  '''

    pass

  def __setattr__(self, key, value):

    '''  '''

    pass
