# -*- coding: utf-8 -*-

'''

  canteen defer
  ~~~~~~~~~~~~~

  utilities for deferring execution.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

from . import runtime


with runtime.Library('karnickel', strict=True) as (library, karnickel):

  ''' Conditionally define defertools. '''


  @karnickel.macro
  def config():
    print 'config'
    __body__


  @karnickel.macro
  def construction(start=False, end=False):
    print 'construction'
    __body__


  @karnickel.macro
  def runtime(start=False, end=False):
    print 'runtime'
    __body__


  karnickel.install_hook()  # -*- install the import hook -*- #

  import pdb; pdb.set_trace()
