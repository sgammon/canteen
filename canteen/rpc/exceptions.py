# -*- coding: utf-8 -*-

"""

  RPC exceptions
  ~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

from . import ServerException
from . import ClientException
from . import Exception as Error


class InternalRPCException(Error):

    """ Base class for all errors in service handlers module. """


class ServiceConfigurationError(InternalRPCException):

    """ When service configuration is incorrect. """


class RequestError(ClientException):

    """ Error occurred when building request. """


class ResponseError(ServerException):

    """ Error occurred when building response. """
