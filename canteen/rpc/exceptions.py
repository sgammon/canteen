# -*- coding: utf-8 -*-

'''

  canteen: RPC exceptions
  ~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''


class Error(Exception):

  ''' Base class for all errors in service handlers module. '''


class ServiceConfigurationError(Error):

  ''' When service configuration is incorrect. '''


class RequestError(Error):

  ''' Error occurred when building request. '''


class ResponseError(Error):

  ''' Error occurred when building response. '''
