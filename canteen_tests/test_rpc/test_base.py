# -*- coding: utf-8 -*-

'''

  base RPC tests
  ~~~~~~~~~~~~~~

  tests canteen's builtin RPC systems.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

'''

# canteen core & model
from canteen import model
from canteen.core import Library

# canteen testing
from canteen.test import FrameworkTest


with Library('protorpc', strict=True) as (library, protorpc):

  # load messages library
  messages = library.load('messages')

  # JSON protocol
  from canteen.rpc.protocol import json as jsonrpc


  class SampleMessage(messages.Message):

    ''' Sample ProtoRPC message. '''

    string = messages.StringField(1)
    integer = messages.IntegerField(2)


  class SampleModel(model.Model):

    ''' Sample Canteen model. '''

    string = basestring
    integer = int

  """
  ## BaseRPCTests
  # Tests the basics of the RPC framework.
  class BaseRPCTests(FrameworkTest):

    ''' Tests basic `canteen.rpc` functionality '''

    def test_exports(self):

      ''' Test basic RPC exports '''

      pass

    def test_service_construction(self):

      ''' Test basic `rpc.Service` construction '''

      pass

    def test_service_mappings(self):

      ''' Test generation of `rpc.Service` mappings '''

      pass


  ## ServiceHandlerTests
  # Tests the base ServiceHandler class.
  class ServiceHandlerTests(FrameworkTest):

    ''' Tests the `rpc.ServiceHandler` class '''

    def test_construct(self):

      ''' Test constructing an `rpc.ServiceHandler` '''

      pass

    def test_add_service(self):

      ''' Test `ServiceHandler.add_service` '''

      pass

    def test_get_service(self):

      ''' Test `ServiceHandler.get_service` '''

      pass

    def test_services_iter(self):

      ''' Test `ServiceHandler.services` as an iterator '''

      pass

    def test_describe_struct(self):

      ''' Test describing `Service` definitions as a dictionary '''

      pass

    def test_describe_json(self):

      ''' Test describing `Service` definitions as JSON '''

      pass

    def test_describe_javascript(self):

      ''' Test describing `Service` definitions via JavaScript '''

      pass

    def test_build_wsgi_application(self):

      ''' Test assembling a WSGI application for `Service` dispatch '''

      pass

    def test_submit_HTTP_HEAD(self):

      ''' Test submitting an `HTTP HEAD` to the RPC layer '''

      pass

    def test_submit_HTTP_PUT(self):

      ''' Test submitting an `HTTP PUT` to the RPC layer '''

      pass

    def test_submit_HTTP_OPTIONS(self):

      ''' Test submitting an `HTTP OPTIONS` to the RPC layer '''

      pass

    def test_submit_HTTP_GET(self):

      ''' Test submitting an `HTTP GET` to the RPC layer '''

      pass

    def test_submit_HTTP_POST(self):

      ''' Test submitting an `HTTP POST` to the RPC layer '''

      pass


  ## AbstractServiceTests
  # Tests the `rpc.AbstractService` class.
  class AbstractServiceTests(FrameworkTest):

    ''' Tests `rpc.AbstractService` '''

    pass


  ## BaseServiceTests
  # Tests the `rpc.Service` class.
  class BaseServiceTests(FrameworkTest):

    ''' Tests `rpc.Service` '''

    pass


  ## ServiceFactoryTests
  # Tests the `rpc.ServiceFactory` class.
  class ServiceFactoryTests(FrameworkTest):

    ''' Tests `rpc.ServiceFactory` '''

    pass


  ## DecoratorTests
  # Tests the `rpc.remote` class.
  class DecoratorTests(FrameworkTest):

    ''' Tests `rpc.remote` '''

    pass
  """
