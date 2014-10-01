# -*- coding: utf-8 -*-

"""

  base RPC tests
  ~~~~~~~~~~~~~~

  tests canteen's builtin RPC systems.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

"""

# stdlib
import json
import inspect

# canteen
from canteen import (rpc, model)
from canteen.core import Library

# canteen testing
from canteen.test import FrameworkTest


with Library('protorpc', strict=True) as (library, protorpc):

  # load messages library
  premote, messages = (library.load('remote'),
                       library.load('messages'))


  class SampleMessage(messages.Message):

    """ Sample ProtoRPC message. """

    string = messages.StringField(1)
    integer = messages.IntegerField(2)


  class BaseRPCTests(FrameworkTest):

    """ Tests basic `canteen.rpc` functionality """

    def test_exports(self):

      """ Test basic RPC exports """

      assert hasattr(rpc, 'VariantField')
      assert hasattr(rpc, 'StringOrIntegerField')
      assert hasattr(rpc, 'Key')
      assert hasattr(rpc, 'Echo')
      assert hasattr(rpc, 'messages')

    def test_export_classes(self):

      """ Test basic RPC class exports """

      assert hasattr(rpc, 'ServiceHandler')
      assert hasattr(rpc, 'Exception')
      assert hasattr(rpc, 'ServerException')
      assert hasattr(rpc, 'ClientException')
      assert hasattr(rpc, 'Exceptions')
      assert hasattr(rpc, 'AbstractService')
      assert hasattr(rpc, 'Service')
      assert hasattr(rpc, 'remote')

    def test_service_construction(self):

      """ Test basic `rpc.Service` construction """


      class SampleService(rpc.Service):
          """ Sample RPC service """

      SampleService()

    def test_service_mappings(self):

      """ Test generation of `rpc.Service` mappings """


      class SampleService(rpc.Service):
          """ Sample RPC service """


      class SampleServiceTwo(rpc.Service):
          """ Sample RPC service 2 """

      mappings = (
        ('/_rpc/sample1', SampleService),
        ('/_rpc/sample2', SampleServiceTwo))

      rpc.service_mappings(mappings)

    def test_service_mappings_with_dict(self):

      """ Test generation of `rpc.Service` mappings from a dict """


      class SampleService(rpc.Service):
          """ Sample RPC service """


      class SampleServiceTwo(rpc.Service):
          """ Sample RPC service 2 """

      mappings = {
        '/_rpc/sample1': SampleService,
        '/_rpc/sample2': SampleServiceTwo}

      rpc.service_mappings(mappings)

    def test_service_mappings_duplicate_uris(self):

      """ Test invalid URIs with service mappings generator """


      class SampleService(rpc.Service):
          """ Sample RPC service """


      class SampleServiceTwo(rpc.Service):
          """ Sample RPC service 2 """

      mappings = (
        ('/_rpc/sample1', SampleService),
        ('/_rpc/sample1', SampleServiceTwo))

      with self.assertRaises(premote.ServiceConfigurationError):
        rpc.service_mappings(mappings)


  class ServiceHandlerTests(FrameworkTest):

    """ Tests the `rpc.ServiceHandler` class """

    def test_construct(self):

      """ Test constructing an `rpc.ServiceHandler` """

      rpc.ServiceHandler()  # pretty simple

    def test_add_service(self):

      """ Test `ServiceHandler.add_service` """


      class SampleService(rpc.Service): pass

      # add service to handler
      handler = rpc.ServiceHandler()
      handler.add_service('sample', SampleService, **{'sample': True})

      return handler, SampleService

    def test_get_service(self):

      """ Test `ServiceHandler.get_service` """

      handler, svc = self.test_add_service()

      # try to get sample service
      sample = handler.get_service('sample')

      assert sample is svc

    def test_services_iter(self):

      """ Test `ServiceHandler.services` as an iterator """

      handler, svc = self.test_add_service()

      # iterate and make sure sample appears
      services = []
      for name, (service, config) in handler.services:
        services.append(service)

      assert svc in services, "failed to find sample in %s" % services

    def test_describe_struct(self):

      """ Test describing `Service` definitions as a dictionary """

      handler, svc = self.test_add_service()

      # describe as dictionary and interrogate
      manifest = handler.describe()
      assert len(manifest)

      sample_item = None
      for i in manifest:
        if i[0] == 'sample':
          sample_item = i

      assert sample_item[0] == 'sample'
      assert sample_item[-1]['sample'] is True

    def test_describe_json(self):

      """ Test describing `Service` definitions as JSON """

      handler, svc = self.test_add_service()

      # describe as dictionary and interrogate
      manifest = json.loads(handler.describe(json=True))
      assert len(manifest)

      sample_item = None
      for i in manifest:
        if i[0] == 'sample':
          sample_item = i

      assert sample_item[0] == 'sample'
      assert sample_item[-1]['sample'] is True

    def test_describe_javascript(self):

      """ Test describing `Service` definitions via JavaScript """

      handler, svc = self.test_add_service()

      # describe as dictionary and interrogate
      manifest = handler.describe(javascript=True)
      assert 'sample' in manifest  # service name
      assert 'true' in manifest  # in config
      assert 'apptools.rpc.service.factory(' in manifest

      manifest = manifest.replace('apptools.rpc.service.factory(', '')
      manifest = manifest.replace(');', '')
      manifest = json.loads(manifest)
      assert len(manifest)

      sample_item = None
      for i in manifest:
        if i[0] == 'sample':
          sample_item = i

      assert sample_item[0] == 'sample'
      assert sample_item[-1]['sample'] is True

    def test_describe_invalid_format(self):

      """ Test describing `Service` definitions with an invalid format """

      handler, svc = self.test_add_service()

      # describe as dictionary and interrogate
      with self.assertRaises(TypeError):
        handler.describe(json=True, javascript=True)

    def test_describe_javascript_with_custom_callable(self):

      """ Test describing `Service` definitions via JavaScript with a custom
          callable """

      handler, svc = self.test_add_service()

      # describe as dictionary and interrogate
      manifest = handler.describe(json=False,
                                  javascript=True,
                                  callable='testing')

      assert 'sample' in manifest  # service name
      assert 'true' in manifest  # in config
      assert 'testing(' in manifest

      manifest = json.loads(manifest.replace('testing(', '').replace(');', ''))
      assert len(manifest)

      sample_item = None
      for i in manifest:
        if i[0] == 'sample':
          sample_item = i

      assert sample_item[0] == 'sample'
      assert sample_item[-1]['sample'] is True

    def test_build_wsgi_application(self):

      """ Test assembling a WSGI application for `Service` dispatch """

      handler, svc = self.test_add_service()

      # describe as dictionary and interrogate
      manifest = handler.describe(json=False, javascript=False)
      assert len(manifest)

      sample_item = None
      for i in manifest:
        if i[0] == 'sample':
          sample_item = i

      assert sample_item[0] == 'sample'
      assert sample_item[-1]['sample'] is True

      # describe as application and interrogate
      wsgi_app = handler.application

      # basic tests
      assert callable(wsgi_app)
      assert inspect.isfunction(wsgi_app)


  ## ServiceFactoryTests
  # Tests the `rpc.ServiceFactory` class.
  class ServiceFactoryTests(FrameworkTest):

    """ Tests `rpc.ServiceFactory` """

    def test_construct(self):

      """ Test construction of a new `ServiceFactory` """


      class SomeService(rpc.Service):
          """ Some sample service. """

      factory = rpc.ServiceFactory.construct(SomeService)
      assert factory
      return factory

    def test_instance_factory(self):

      """ Test instance creation through `ServiceFactory` """

      factory = self.test_construct()
      instance = factory()

      assert factory
      assert instance


  ## DecoratorTests
  # Tests the `rpc.remote` class.
  class DecoratorTests(FrameworkTest):

    """ Tests `rpc.remote` """

    def test_construct(self):

      """ Test construction of a new `rpc.remote` wrapper """

      r = rpc.remote('registered', version=1)

      assert r.name == 'registered'
      assert r.config['version'] == 1
      return r

    def test_wrap_raw(self):

      """ Test wrapping a `Service` with `rpc.remote` directly """

      r = self.test_construct()


      class RegisteredService(rpc.Service):
          """ Service mock for testing registration """

      klass = r(RegisteredService)

      assert r.target is klass
      assert rpc.ServiceHandler.get_service('registered') is klass

      return klass, r

    def test_wrap_service(self):

      """ Test wrapping a `Service` with `rpc.remote.service` """

      klass, r = self.test_wrap_raw()

      wrap = r.service(klass)
      assert callable(wrap)

    def test_wrap_method(self):

      """ Test wrapping a method with `rpc.remote.method` """


      class SampleMessage(messages.Message):

        """ Mock message """

        string = messages.StringField(1)
        integer = messages.IntegerField(2)


      class RegisteredService(rpc.Service):

        """ Service mock for testing registration """

        @rpc.remote.method(SampleMessage)
        def registered_method(self, request):  # pragma: no cover

          """ I am a registered service message. """

          request.integer += 1
          request.string += ", world!"
          return request

      assert callable(RegisteredService.registered_method)
      return RegisteredService, SampleMessage

    def test_wrap_method_models(self):

      """ Test wrapping a method with `rpc.remote.method` that uses Canteen
          models """

      class SampleRequest(model.Model):

        """ Mock request """

        string = basestring
        integer = int

      class SampleResponse(model.Model):

        """ Mock response """

        string = basestring
        integer = int

      @rpc.remote.service('registered')
      class RegisteredService(rpc.Service):

        """ Service mock for testing registration """

        @rpc.remote.method(SampleRequest, SampleResponse)
        def registered_method(self, request):  # pragma: no cover

          """ I am a registered service message. """

          return SampleResponse(**{
            'string': request.string + ', world!',
            'integer': request.integer + 1
          })

      assert callable(RegisteredService.registered_method)
      return RegisteredService, SampleRequest, SampleResponse

    def test_wrap_method_dispatch(self):

      """ Test dispatching an RPC directly through a wrapped
          `rpc.remote.method` """

      RegisteredService, SampleMessage = self.test_wrap_method()

      # make message
      request = SampleMessage(string='Hello', integer=10)

      # dispatch
      result = RegisteredService().registered_method(request)

      assert result.string == 'Hello, world!'
      assert result.integer == 11
      assert isinstance(result, SampleMessage)

    def test_wrap_method_dispatch_models(self):

      """ Test dispatching an RPC with models through a wrapped
         `rpc.remote.method` """

      RegisteredService, SampleRequest, SampleResponse = (
          self.test_wrap_method_models())

      # make message
      request = SampleRequest(string='Hello', integer=10)
      r = request.to_message()

      # dispatch
      result = RegisteredService().registered_method(r)

      assert result.string == 'Hello, world!'
      assert result.integer == 11
      assert isinstance(result, messages.Message), (
          "expected response class %s, got %s" % (messages.Message, result))
