# -*- coding: utf-8 -*-

"""

  RPC
  ~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import abc
import copy

# canteen
from canteen import core
from canteen import base
from canteen import model

# canteen core
from canteen.core import runtime
from canteen.core import injection

# canteen HTTP
from canteen.logic import http

# canteen util
from canteen.util import decorators
from canteen.util import struct as datastructures


with core.Library('protorpc', strict=True) as (library, protorpc):

  #### ==== Dependencies ==== ####

  # remote / message packages
  from protorpc import remote as premote
  from protorpc import registry as pregistry

  # message packages
  from protorpc import messages as pmessages
  from protorpc.messages import Field as ProtoField
  from protorpc.messages import Message as ProtoMessage

  # message types
  from protorpc import message_types as pmessage_types
  from protorpc.message_types import VoidMessage as ProtoVoidMessage

  # WSGI internals
  from protorpc.wsgi import util as pwsgi_util
  from protorpc.wsgi import service as pservice


  ## Globals
  _RPC_BASE_URI = '/_rpc/'


  #### ==== Message Fields ==== ####

  class VariantField(ProtoField):

      """ Field definition for a completely variant field. Allows containment
          of any valid Python value supported by Protobuf/ProtoRPC. """

      VARIANTS = frozenset([pmessages.Variant.DOUBLE, pmessages.Variant.FLOAT,
                            pmessages.Variant.BOOL, pmessages.Variant.INT64,
                            pmessages.Variant.UINT64, pmessages.Variant.SINT64,
                            pmessages.Variant.INT32, pmessages.Variant.UINT32,
                            pmessages.Variant.SINT32, pmessages.Variant.STRING,
                            pmessages.Variant.BYTES, pmessages.Variant.MESSAGE,
                            pmessages.Variant.ENUM])

      DEFAULT_VARIANT = pmessages.Variant.STRING

      type = (int, long, bool, basestring, dict, pmessages.Message)


  class StringOrIntegerField(ProtoField):

      """ Field definition for a field that can contain either a string or
          integer. Usually used for key names/IDs or message IDs/hashes. """

      VARIANTS = frozenset([pmessages.Variant.STRING, pmessages.Variant.DOUBLE,
                            pmessages.Variant.INT64, pmessages.Variant.INT32,
                            pmessages.Variant.UINT64, pmessages.Variant.UINT32])

      DEFAULT_VARIANT = pmessages.Variant.STRING

      type = (int, long, basestring, dict, pmessages.Message)


  #### ==== Message Classes ==== ####

  class Key(ProtoMessage):

      """ Message for a :py:class:`canteen.model.Key`. """

      encoded = pmessages.StringField(1)  # encoded (`urlsafe`) key
      kind = pmessages.StringField(2)  # kind name for key
      id = StringOrIntegerField(3)  # integer or string ID for key
      namespace = pmessages.StringField(4)  # string namespace for key
      parent = pmessages.MessageField('Key', 5)  # recursive key message


  class Echo(ProtoMessage):

      """ I am rubber and you are glue... """

      message = pmessages.StringField(1, default='Hello, world!')


  ## expose message classes alias
  messages = datastructures.WritableObjectProxy(**{

      # canteen-provided messages
      'Key': Key,  # message class for a canteen model key
      'Echo': Echo,  # echo message defaulting to `hello, world` for testing

      # builtin messages
      'Message': ProtoMessage,  # top-level protorpc message class
      'VoidMessage': ProtoVoidMessage,  # top-level protorpc void message

      # specific types
      'Enum': pmessages.Enum,  # enum descriptor / definition class
      'Field': pmessages.Field,  # top-level protorpc field class
      'FieldList': pmessages.FieldList,  # top-level protorpc field list class

      # field types
      'VariantField': VariantField,  # generic hold-anything property
      'BooleanField': pmessages.BooleanField,  # boolean true/false field
      'BytesField': pmessages.BytesField,  # low-level binary-safe string field
      'EnumField': pmessages.EnumField,  # field for referencing an `Enum` class
      'FloatField': pmessages.FloatField,  # field for a floating point number
      'IntegerField': pmessages.IntegerField,  # field for an integer
      'MessageField': pmessages.MessageField,  # field for a sub-message
      'StringField': pmessages.StringField,  # field for unicode or ASCII
      'DateTimeField': pmessage_types.DateTimeField  # field for datetime types

  })


  def service_mappings(services, registry_path='/_rpc/meta', protocols=None):

    """ Generates mappings from `url -> service` for registered Canteen RPC
        services.

        Takes an iterable of URL and service mappings, wraps with appropriate
        WSGI utilities, and registers with registry service for Endpoints/meta
        integration.

        :param services: Iterable of services, preferably a ``list`` of
          ``tuples``, where each is in the format ``(url, service)``. ``url``
          should be a relative prefix for matching requests, like
          ``/_rpc/hello`` for something called ``HelloService``.

        :param registry_path: Path prefix for ``RegistryService``, which returns
          metadata about registered RPC services. Required for integration with
          Google Cloud Endpoints or the various ProtoRPC client-side library
          generation options out there.

        :param protocols: Protocols to use for dispatching services. Custom
          protocol implementations are supported and two are shipped with
          canteen - ``JSON`` and ``msgpack`` RPC formats (note: not necessarily
          affiliated with any standards that are actually called "msgpack-rpc"
          or "jsonrpc").

        :returns: WSGI application prepared by :py:mod:`protorpc`, which, upon
          dispatch, will attempt to delegate response to the first matching
          ``Service`` implementation, as governed by the mappings generated in
          this function from ``services``. """

    if not protocols:
      # load canteen builtin protocols
      from canteen.base import protocol
      protocols = protocol.Protocol.mapping

    if isinstance(services, dict):
      services = services.iteritems()

    final_mapping, paths, registry_map = (
      [],
      set(),
      {} if registry_path else None
    )

    for service_path, service_factory in services:
      service_class = service_factory.service_class if (
        hasattr(service_factory, 'service_class')) else service_factory

      if service_path not in paths:
        paths.add(service_path)
      else:
        raise premote.ServiceConfigurationError(
          'Path %r is already defined in service mapping' %
          service_path.encode('utf-8'))

      if registry_map is not None: registry_map[service_path] = service_class
      final_mapping.append((
        pservice.service_mapping(*(
          service_factory, service_path), protocols=protocols)))

    if registry_map is not None:
      final_mapping.append(pservice.service_mapping(*(
        pregistry.RegistryService.new_factory(registry_map), registry_path),
            protocols=protocols))

    return pwsgi_util.first_found(final_mapping)


  @http.url('rpc', (
    r'%s<string:version>/<string:service>.<string:method>' % _RPC_BASE_URI))
  class ServiceHandler(base.Handler):

    """ Builtin concrete :py:class:`base.Handler` for use with RPC services. As
        services are bound to names, they are registered here and eventually
        mapped URLs are generated (via `service_mappings`).

        Normally this handler is mapped at ``<version>/<service>.<method>``,
        which supports both service types ('concrete' and 'registry') at the
        following URLs (with examples inline):

        - concrete: ``v1/hello.hi`` for a ``HelloService`` with ``hi`` method
        - meta: ``meta/registry.services`` to describe a service's methods """

    __services__ = {}  # holds services mapped to their names

    @classmethod
    def add_service(cls, name, service, config=None, **kwargs):

      """ Add a service to this handler's local dispatch registry.
          Called from ``@rpc.service`` to mount a service to dispatch.

          :param name: Simple string name for the service. For instance,
            ``hello`` for ``HelloService``.

          :param service: Service class to be registered.

          :param config: Configuration can be passed as a dictionary
            (at ``config``) or with ``kwargs``, which override items in
            ``config``.

          :returns: The service class passwd at ``service``. """

      config = config or {}
      config.update(kwargs)
      cls.__services__[name] = (service, config or {})
      return service

    @decorators.classproperty
    def services(cls):

      """ Iterator for all locally-registered services, presented as
          a class-level property.

          :yields: Each named service, in the tupled format
            ``name, service``, much like ``dict.iteritems``. """

      for name in sorted(cls.__services__.iterkeys()):
        yield name, cls.__services__[name]

    @classmethod
    def get_service(cls, name):

      """ Retrieve a locally-registered service by name.

          :param name: Short name for the service. For instance,
            ``hello`` for ``HelloService``.

          :returns: Registered ``rpc.Service`` class at that name,
            or ``None`` if no matching service could be located. """

      if name in cls.__services__:
        return cls.__services__[name][0]

    @classmethod
    def describe(cls, json=False,
                      javascript=False,
                      callable='apptools.rpc.service.factory'):

      """ Describe locally-registered services in various formats.
          Exposed to template context as ``services.describe``, so that
          frontends can easily be notified of supported RPC services.

          Omitting both ``json`` and ``javascript`` will return a ``list``
          of ``tuples`` describing each service, as ``(name, methods, config)``.

          Passing ``json`` *and* ``javascript`` is unsupported and raises
          a ``TypeError`` describing your foolishness.

          :param json: Describe the services as a JSON string, suitable for
            placement on an HTML page. Boolean, defaults to ``False``.

          :param javascript: Generate JS that calls a function (assumed to
            already be present on ``window``) with a structure describing
            locally registered services, suitable for placement on an HTML
            page. Boolean, defaults to ``False``.

          :param callable: Opportunity to change the frontend callable function
            that will be passed the service manifest. Defaults to the hard-coded
            value ``apptools.rpc.service.factory`` for backwards compatibility.

          :returns: ``list`` of ``tuples`` if requesting structured description,
            or a JSON string of that structure if ``json=True`` is passed, or JS
            code invoked with that JSON structure if ``javascript=True`` is
            passed. """

      _services = []
      for name, service in cls.services:
        service, config = service
        _services.append((
          name,  # service shortname

          # service methods
          tuple((name for name in service.all_remote_methods().iterkeys())),

          # service config
          config or {}
        ))

      if json and javascript:
        raise TypeError('Please pick between "JSON" and "JavaScript"'
                        ' output for services.')

      if json:  # generate JSON only?
        import json as serializer
        return serializer.dumps(_services)

      if javascript:  # generate javascript?
        import json as serializer
        return "%s(%s);" % (callable, serializer.dumps(_services))
      return _services  # or return raw?

    @decorators.classproperty
    def application(cls):

      """ Utility for generating a WSGI application capable of dispatching
          locally-registered services on ``ServiceHandler``, exposed as a class-
          level property.

          Uses :py:mod:`protorpc`'s fantastic `wsgi.utils.first_found`, which
          will dispatch `rpc.Service` applications one at a time until a non-404
          error occurs, in which case response is delegated to that application.

          If no application can be found to match the given WSGI state, an
          ``HTTP 404`` is raised.

          :returns: Prepared ``protorpc.wsgi.utils.first_found`` WSGI
            application closure.  """

      _services = []
      for name, service in cls.services:

        service, config = service
        service_factory = service.new_factory(config=config)

        # Update docstring so that it is easier to debug.
        full_class_name = '%s.%s' % (service.__module__, service.__name__)
        if __debug__:
          service_factory.func_doc = (
              'Creates new instances of service %s.\n\n'
              'Returns:\n'
              '  New instance of %s.'
              % (service.__name__, full_class_name))

        # Update name so that it is easier to debug the factory function.
        service_factory.func_name = '%s_service_factory' % service.__name__

        service_factory.service_class = service

        # resolve service version
        _version = config.get('version', 'v1')
        if isinstance(_version, int): _version = 'v' + str(_version)
        _services.append((r'/_rpc/%s/%s' % (_version, name), service_factory))

      return service_mappings(_services, registry_path='/_rpc/meta/registry')

    def OPTIONS(self, version, service, method):

      """ Dispatch handler for ``HTTP OPTIONS`` requests. Specifies available
          HTTP methods as ``OPTIONS`` and ``POST``, since (by default) only
          RPC-like functionality is supported.

          :param version: Service version, as specified in the URL.
          :param service: Service name, as specified in the URL.
          :param method: Service method to dispatch, as specified in the URL.

          :returns: Suitable HTTP response for an ``HTTP OPTIONS`` request. """

      # @TODO(sgammon): HTTP OPTIONS integration testing for services
      return self.response('OPTIONS, POST')  # pragma: no cover

    def POST(self, version, service, method):  # pragma: no cover

      """ Dispatch handler for ``HTTP POST`` requests. Main entrypoint into
          the RPC framework via HTTP, as requests are ``POST``ed in a supported
          ``Content-Type`` for an attached ``Protocol``.

          :param version: Service version, as specified in the URL.
          :param service: Service name, as specified in the URL.
          :param method: Service method to dispatch, as specified in the URL.

          :returns: Suitable HTTP response for an ``HTTP POST`` request.  """

      # @TODO(sgammon): HTTP POST integration testing for services
      _status, _headers = None, None

      def _respond(status, headers):  # pragma: no cover

        """ Inner response closure that overrides normal ``start_response``.

            :param status: HTTP status for response.
            :param headers: Iterable of ``(name, value)`` pairs for HTTP
            response headers. """

        _status, _headers = status, headers

      # delegate to service application
      return self.response.__class__((
        self.application(self.environment, _respond)), **{
        'status': _status,
        'headers': _headers
      })

    GET = POST


  class Exception(premote.ApplicationError):

      """ Base RPC exception class, used to indicate an application-level error.
          Backed by ProtoRPC's :py:class:`remote.ApplicationError`. """


  class ServerException(premote.ServerError):

      """ Base RPC exception class, used to indicate a server-side error.
          Backed by ProtoRPC's :py:class:`remote.ServerError`. """


  class ClientException(premote.RequestError):

      """ Base RPC exception class, used to indicate a client-side error. Backed
          by ProtoRPC's :py:class:`remote.RequestError`. """


  class Exceptions(datastructures.ObjectProxy):

      """ Datastructure used to house remote-capable RPC exceptions, and for
          expression of error types in meta APIs. """


  class AbstractService(premote.Service):

    """ Abstract class that provides basic Canteen integration for remote
        services. Handles MRO injection and ABC enforcement."""

    class __metaclass__(premote.Service.__metaclass__):

      """ Inline metaclass for `AbstractService` that injects a DI delegate into
          the MRO chain. """

      __delegate__ = None  # dependency injection delegate class

      def mro(cls):

        """ Inject a DI delegate (generated at `cls.delegate`) to enable
            MRO-based injection.

            :returns: Assembled MRO chain (a ``list``). """

        # noinspection PyCallByClass
        chain = type.mro(cls)

        if not premote.StubBase in cls.__bases__:
          if cls.__name__ is "AbstractService":
            # wrap delegate deep in the root
            return chain[0:-1] + [cls.delegate()] + chain[-1:]
        return chain  # it's a stub or something else - don't touch anything

      def delegate(cls):

        """ Generate a DI delegate suitable for use as a window into the main
            DI pool from ``AbstractService``.

            :returns: Bound :py:class:`injection.Delegate`. """

        cls.__class__.__delegate__ = injection.Delegate.bind(cls)
        return cls.__class__.__delegate__

    @abc.abstractproperty
    def exceptions(self):  # pragma: no cover

      """ Abstract property requiring the specification of expected exceptions
          from a remote service.

          :raises NotImplementedError: Always, as this property is abstract. """

      raise NotImplementedError('Property `AbstractService.exceptions`'
                                ' requires implementation by a concrete'
                                ' subclass and cannot be invoked directly.')


  class Service(AbstractService):

    """ Base remote service class, used as an extension point for Canteen
        application developers to create their own remotely-accessible RPC
        services. """

    __state__ = None  # local state
    __config__ = None  # local configuration

    def __init__(self, config=None, **kwargs):

      """ Initialize a new ``Service`` instance, optionally overlaying
          configuration with ``config`` or ``kwargs``, which override items in
          ``config``.

          :param config: Positional opportunity to specify service
            configuration. """

      config = config or {}
      config.update(kwargs)
      self.__config__ = config

    ## = property accessors = ##
    state = property(lambda self: self.__state__)  # accessor for __state__
    config = property(lambda self: self.__config__)  # accessor for __config__
    platform = property(lambda self: self.__bridge__)  # accessor for __bridge__

    @classmethod
    def new_factory(cls, *args, **kwargs):

      """ Classmethod for constructing a new ``ServiceFactory`` to wrap this
          ``Service`` class. Passes positional and keyword arguments for later
          use in ``Service.__init__``.

          :returns: Constructed ``ServiceFactory`` instance. """

      return ServiceFactory.construct(cls, *args, **kwargs)

    def initialize_request_state(self, state):  # pragma: no cover

      """ Initialize this service with ``state`` handed-in by ProtoRPC's
          underlying plumbing.

          :param state: State to attach locally. Always a descendent of
            :py:class:`remote.RequestState`, and usually an instance of
            :py:class:`remote.HttpRequestState` (which is used when running over
            HTTP, obviously).

          :returns: Nothing. """

      # @TODO(sgammon): full-cycle HTTP RPC testing
      self.__state__ = state
      if hasattr(self, 'initialize'):
        try:  # @TODO(sgammon): better logging here
          self.initialize(state)  # hand down to initialize hook
        except Exception as e:
          import traceback; traceback.print_exc()
          if __debug__: raise


  class ServiceFactory(object):

    """ Specifies an object that wraps an ``rpc.Service`` class and encapsulates
        a static set of ``args`` and ``kwargs`` to construct instaces of that
        wrapped ``Service``. """

    service = Service  # service class to factory
    args, kwargs = None, None  # service init args

    def __new__(cls, **kwargs):

      """ New instances requested of this ``cls`` are redirected to the
          constructor for the locally encapsulated ``Service`` class.

          Updated ``kwargs`` can be passed via this constructor, to be overlayed
          on ``cls``-level ``kwargs`` before being handed to the target's
          constructor.

          :returns: Constructed ``Service`` object. """

      _kargs = copy.deepcopy(cls.kwargs)
      _kargs.update(kwargs)

      return cls.service(*(cls.args or tuple()), **(_kargs or {}))

    @classmethod
    def construct(cls, service, *args, **kwargs):

      """ Construct a new, dynamic ``ServiceFactory`` subclass dedicated to
          wrapping ``service``, optionally specifying positional ``args`` and
          keyword ``kwargs``.

          :param service: ``Service`` class to wrap with the newly-constructed
            ``ServiceFactory`` subclass.

          :returns: Dynamically-generated ``ServiceFactory`` class wrapping
            given ``service`` class. """

      return type(service.__name__ + 'Factory', (cls,), {
        'args': args,
        'kwargs': kwargs,
        'service': service
      })

    # shortcut to the ``service_class``
    service_class = decorators.classproperty(lambda cls: cls.service)

    # shortcut to alias f() to s()
    __call__ = lambda self: self.service(*self.args, **self.kwargs)


  class remote(object):

    """ Utility class that provides utilities for registering and mounting
        ``remote`` methods, services, and configuration. """

    name = None  # string name for target
    config = None  # config items for target
    target = None  # contains a service if wrapping one

    def __init__(self, name, expose='public', **config):

      """ Initialize this instance of ``remote`` with a string ``name`` and
          exposure policy (at ``expose``, which defaults to 'public').

          Configuration can be passed as kwargs. """

      self.name, self.config = name, config

    @classmethod
    def register(cls, name_or_message, response=None, **config):

      """ Internal function used to register this remote object, bound to either
          a ``name`` (if the target is a ``Service``) or a ``request`` and
          ``response`` message pair.

          Configuration can be passed as kwargs.

          :returns: Closured function designed to wrap the target callable with
            a routine to register it before construction. """

      if isinstance(name_or_message, basestring):
        name, request = name_or_message, None
      else:
        name, request = None, name_or_message

      if not name:

        request_klass, response_klass = None, None
        if isinstance(request, type) and issubclass(request, model.Model):
          request_klass = response_klass = request.to_message_model()

        if response and response != request:
          if isinstance(response, type) and issubclass(response, model.Model):
            response_klass = response.to_message_model()

        request_klass, response_klass = (
          request_klass or name_or_message,
          response_klass or (response or name_or_message)
        )

        def _remote_method(method):

          """ Closure to wrap the target ``method`` at construction time with
              appropriate tooling to execute remote RPCs.

              :param method: Remote-capable method to be wrapped.

              :returns: Wrapped closure ``_respond`` that, when called,
                dispatches the target ``method``. """

          def _respond(self, _request_message):

            """ Inner closure designed to wrap the raw remote ``method`` and
                enforce validation/conversion of ProtoRPC types to native Python
                ones.

                Also handles conversion in/out of Canteen models, if the remote
                method so chooses, by binding to ``canteen.Model`` subclasses
                instead of ProtoRPC ``message.Message``s.

                :param _request_message: Remotely-submitted ``request`` to
                (potentially) be converted and submitted to inner service
                ``method``.

                :returns: Result of calling ``method`` with ``_request_message``
                  as the originating request, so long as the request was
                  successfully executed and passed all client-related
                  constraints. """

            if isinstance(request, type) and issubclass(request, model.Model):
              # convert incoming message to model
              result = method(self, request.from_message(_request_message))

            else:
              # we're using regular messages always
              result = method(self, _request_message)

            # convert outgoing message to model if it isn't already
            if isinstance(result, model.Model):
              return result.to_message()
            return result

          # wrap responder
          wrapped = premote.method(request_klass, response_klass)(_respond)

          # make things transparent
          wrapped.__name__, wrapped.__doc__, wrapped.__inner__ = (
            method.__name__,
            method.__doc__,
            method)

          _respond.__inner__ = wrapped

          # quack quack
          _respond.__name__, _respond.__doc__, _respond.remote = (
            method.__name__,
            method.__doc__,
            wrapped.remote)

          # just for backup
          wrapped.__remote_name__, wrapped.__remote_doc__ = (
            method.__name__,
            method.__doc__,)

          # add remote info
          wrapped.__remote__ = wrapped.remote

          return _respond
        return _remote_method

      # wrap wrap wrapper
      config['expose'] = config.get('expose', 'public')
      return cls(name, **config)

    # shorthand for `cls.register` with `expose=public`
    public = lambda cls, *args, **config: (
      cls.register(*args, expose='public', **config))

    # shorthand for `cls.register` with `expose=private`
    private = lambda cls, *args, **config: (
      cls.register(*args, expose='private', **config))

    # aliases for `cls.register`
    method = service = register

    def __call__(self, target):

      """ Callable wrapped for ``Service`` classes that is dispatched as part of
          the construction/decorator flow. Adds hooks to local
          ``ServiceHandler`` for the locally-bound ``target`` ``Service`` class.

          :param target: ``Service`` class to be registered and bound.

          :returns: ``target``, after executing hooks and registering. """

      self.target = target

      # finally, register the service (if it's a service class)
      if isinstance(target, type) and issubclass(target, Service):

        # call service registration hooks
        runtime.Runtime.execute_hooks('rpc-service', service=target)

        # call method registration hooks
        for method in target.all_remote_methods():  # pragma: no cover
          runtime.Runtime.execute_hooks('rpc-method',
                                        service=target,
                                        method=method)

        ServiceHandler.add_service(self.name, target, **self.config)

      return target


  __all__ = ('Service',
             'remote',
             'ServiceHandler',
             'service_mappings',
             'messages',
             'Key',
             'Echo',
             'VariantField',
             'protocol',
             'exceptions')
