# -*- coding: utf-8 -*-

"""

  model tests
  ~~~~~~~~~~~

  tests canteen's model classes.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import abc
import json
import inspect

# appconfig
try:
  import config; _APPCONFIG = True
except ImportError as e:  # pragma: no cover
  _APPCONFIG = False
else:  # pragma: no cover
  # set debug mode for all model-related stuff
  class Config(object):
    config = {}
    debug = True
  config = Config()
  config.config = {}

  if 'canteen.model' not in config.config:
    config.config['canteen.model'] = {}
  config.config['canteen.model']['debug'] = True
  for k in filter(lambda x: x.startswith('canteen.model'),
                              config.config.iterkeys()):
    config.config[k]['debug'] = True

# canteen model API
from canteen import model, core
from canteen.model import adapter
from canteen.model import exceptions

# canteen tests
from canteen.test import FrameworkTest

# canteen utils
from canteen.util import struct as datastructures


## == Test Models == ##

class TestCar(model.Model):

  """ An automobile. """

  make = basestring, {'indexed': True}
  model = basestring, {'indexed': True}
  year = int, {'choices': xrange(1900, 2015)}
  color = basestring, {'choices': (
                        'blue', 'green', 'red', 'silver', 'white', 'black')}


class TestPerson(model.Vertex):

  """ A human being. """

  firstname = basestring, {'indexed': True}
  lastname = basestring, {'indexed': True}
  active = bool, {'default': True}
  cars = TestCar, {'repeated': True}
  cars_ref = model.Key, {'repeated': True}
  cars_embedded = TestCar, {'repeated': True, 'embedded': True}


class Friendship(TestPerson > TestPerson):

  """ A friendship between people. """

  year_met = int


## ModelTests
class ModelTests(FrameworkTest):

  """ Tests `model.Model` and `model.AbstractModel`. """

  def test_construct_model(self):

    """ Test constructing a `Model` manually """

    # construct our car record
    car = TestCar(make='BMW', model='M3', year=2013, color='white')

    # construct our person record
    person = TestPerson()
    person.firstname = 'John'
    person.cars = [car]

    # perform tests
    self.assertIsInstance(car, TestCar)
    self.assertIsInstance(person, TestPerson)
    self.assertEqual(person.firstname, 'John')
    self.assertIsInstance(person.cars, list)
    self.assertEqual(len(person.cars), 1)
    self.assertIsInstance(person.cars[0], TestCar)

    # test defaults
    self.assertEqual(person.active, True)

    # test unsets
    self.assertEqual(person.lastname, None)

    # test __repr__
    cls = str(TestPerson)
    obj = str(person)

    # test class representations
    self.assertTrue(("Person" in cls))
    self.assertTrue(("lastname" in cls))
    self.assertTrue(("firstname" in cls))

    # test object representations
    self.assertTrue(("Person" in obj))
    self.assertTrue(("lastname" in obj))
    self.assertTrue(("firstname" in obj))
    self.assertTrue(("John" in obj))

  def test_invalid_model_adapter(self):

    """ Test using invalid model adapter, which should raise `RuntimeError` """

    with self.assertRaises(RuntimeError):

      ## InvalidAdapterModel
      # Tests an invalid, but explicitly listed, model adapter.
      class InvalidAdapterModel(model.Model):

        __adapter__ = 'DumbInvalidModelAdapter'

        prop1 = basestring

  def test_model_inheritance(self):

    """ Test proper inheritance structure for `Model` """

    self.assertTrue(issubclass(TestCar, model.Model))
    self.assertTrue(issubclass(TestPerson, model.Model))
    self.assertTrue(issubclass(model.Model, model.AbstractModel))

  def test_model_schema(self):

    """ Test that there's a proper schema spec on `Model` """

    # check lookup
    self.assertTrue(hasattr(TestPerson, '__lookup__'))
    self.assertIsInstance(TestPerson.__lookup__, frozenset)

    # check property descriptors
    self.assertTrue(hasattr(TestPerson, 'firstname'))
    self.assertTrue(hasattr(TestPerson, 'lastname'))
    self.assertTrue(hasattr(TestPerson, 'cars'))

    # check kind
    self.assertTrue(hasattr(TestPerson, 'kind'))
    self.assertIsInstance(TestPerson.kind(), basestring)

    # check set/get
    self.assertTrue(hasattr(TestPerson, '_get_value'))
    self.assertTrue(hasattr(TestPerson, '_set_value'))
    self.assertTrue(inspect.ismethod(TestPerson._get_value))
    self.assertTrue(inspect.ismethod(TestPerson._set_value))

    # check key
    self.assertTrue(hasattr(TestPerson, 'key'))
    self.assertTrue(hasattr(TestPerson(), '__key__'))

    # should not have key until instantiation
    self.assertTrue((not hasattr(TestPerson, '__key__')))

  def test_model_set_attribute(self):

    """ Test setting an unknown and known attribute on `Model` """

    # try construction assignment
    john = TestPerson(firstname='John')
    self.assertEqual(john.firstname, 'John')

    # re-assign
    john.firstname = 'Blabs'
    self.assertEqual(john.firstname, 'Blabs')

    # try assigning missing property
    with self.assertRaises(AttributeError):
      john.blabs = 'John'

  def test_model_adapter(self):

    """ Test that adapter is attached correctly to `Model` """

    # make sure it's on the classlevel
    self.assertTrue(hasattr(TestPerson, '__adapter__'))
    self.assertIsInstance(TestPerson.__adapter__, adapter.ModelAdapter)

  def test_model_stringify(self):

    """ Test the string representation of a `Model` object """

    self.assertIsInstance(TestPerson().__repr__(), basestring)

  def test_model_kind(self):

    """ Test that `Model.kind` is properly set """

    # test class-level kind
    self.assertIsInstance(TestPerson.kind(), basestring)
    self.assertEqual(TestPerson.kind(), "TestPerson")

    # test object-level kind
    john = TestPerson()
    self.assertIsInstance(john.kind(), basestring)
    self.assertEqual(john.kind(), "TestPerson")

  def test_abstract_model(self):

    """ Test that `AbstractModel` works abstractly """

    # make sure it's ABC-enabled
    self.assertTrue((not isinstance(model.Model, abc.ABCMeta)))

    # try directly-instantiation
    with self.assertRaises(exceptions.AbstractConstructionFailure):
      (model.AbstractModel())

  def test_concrete_model(self):

    """ Test that `Model` works concretely """

    ## test simple construction
    self.assertIsInstance(TestPerson(), TestPerson)


    class SampleTestModel(model.Model):

      """ Test parent model class. """

      parent = basestring


    class SampleSubModel(SampleTestModel):

      """ Test child model class. """

      child = basestring

    ## test properties
    self.assertTrue(hasattr(SampleTestModel, 'parent'))
    self.assertTrue((not hasattr(SampleTestModel, 'child')))

    ## test submodel properties
    self.assertTrue(hasattr(SampleSubModel, 'child'))
    self.assertTrue(hasattr(SampleSubModel, 'parent'))

    ## test recursive subclassing
    self.assertIsInstance(SampleTestModel(), model.Model)
    self.assertIsInstance(SampleSubModel(), SampleTestModel)
    self.assertIsInstance(SampleSubModel(), model.Model)

  def test_model_to_dict(self, method='to_dict'):

    """ Test flattening a `Model` into a raw dictionary """

    # sample person
    p = TestPerson(firstname='John')
    raw_dict = getattr(p, method)()

    if method == 'to_dict':
      # try regular to_dict
      self.assertEqual(len(raw_dict), 2)
      self.assertIsInstance(raw_dict, dict)
      self.assertEqual(raw_dict['firstname'], 'John')  # we set this explicitly

      # this is defaulted, should export
      self.assertEqual(raw_dict['active'], True)

      with self.assertRaises(KeyError):
        raw_dict['lastname']
    return raw_dict

  def test_model_update_with_dict(self):

    """ Test updating a `Model` from a `dict` """

    # sample person
    p = TestPerson(firstname='John')
    update = {
      'firstname': 'Sup',
      'lastname': 'Bleebs'
    }

    p.update(update)

    assert p.firstname == 'Sup'
    assert p.lastname == 'Bleebs'

  def test_model_to_dict_schema(self):

    """ Test flattening a `Model` class into a schema dictionary """

    schema = TestPerson.to_dict_schema()
    assert 'firstname' in schema
    assert isinstance(schema['firstname'], model.Property)
    assert schema['firstname']._basetype == basestring

  def test_model_to_dict_all_arguments(self, method='to_dict'):

    """ Test using `Model.to_dict` with the `all` flag """

    # sample person
    p = TestPerson(firstname='John')
    all_dict = getattr(p, method)(_all=True)

    if method == 'to_dict':
      # test dict with `all`
      self.assertEqual(len(all_dict), len(p.__lookup__))
      self.assertEqual(all_dict['firstname'], 'John')
      self.assertEqual(all_dict['lastname'], None)
      self.assertEqual(all_dict['active'], True)
    return all_dict

  def test_model_to_dict_with_filter(self, method='to_dict'):

    """ Test using `Model.to_dict` with a filter function """

    # sample person
    p = TestPerson(firstname='John')

    # should filter out 'active'
    filtered_dict = getattr(p, method)(filter=lambda x: len(x[0]) > 7)

    if method == 'to_dict':
      # test filter
      self.assertEqual(len(filtered_dict), 1)
      self.assertIsInstance(filtered_dict, dict)
      self.assertEqual(filtered_dict['firstname'], 'John')

      with self.assertRaises(KeyError):
        filtered_dict['active']
    return filtered_dict

  def test_model_to_dict_with_include(self, method='to_dict'):

    """ Test using `Model.to_dict` with an inclusion list """

    # sample person
    p = TestPerson(firstname='John')
    included_dict = getattr(p, method)(include=('firstname', 'lastname'))

    if method == 'to_dict':
      # should still include `lastname` as 'None'
      self.assertEqual(len(included_dict), 2)
      self.assertIsInstance(included_dict, dict)
      self.assertEqual(included_dict['firstname'], 'John')
      self.assertEqual(included_dict['lastname'], None)

      with self.assertRaises(KeyError):
        included_dict['active']  # should not include `active`
    return included_dict

  def test_model_to_dict_with_exclude(self, method='to_dict'):

    """ Test using `Model.to_dict` with an exclusion list """

    # sample person
    p = TestPerson(firstname='John')
    excluded_dict = getattr(p, method)(exclude=('active',))

    if method == 'to_dict':
      # test exclude
      self.assertEqual(len(excluded_dict), 1)
      self.assertIsInstance(excluded_dict, dict)
      self.assertEqual(excluded_dict['firstname'], 'John')

      with self.assertRaises(KeyError):
        excluded_dict['active']  # should not include `active`
    return excluded_dict

  def test_model_to_dict_with_map(self, method='to_dict'):

    """ Test using `Model.to_dict` with a map function """

    # sample person
    p = TestPerson(firstname='John')
    mapped_dict = getattr(p, method)(
                             map=lambda x: tuple([x[0] + '-cool', x[1]]))

    if method == 'to_dict':
      # test map
      self.assertEqual(len(mapped_dict), 2)
      self.assertIsInstance(mapped_dict, dict)
      self.assertEqual(mapped_dict['firstname-cool'], 'John')
      self.assertEqual(mapped_dict['active-cool'], True)
    return mapped_dict

  def test_model_to_dict_convert_keys(self):

    """ Test flattening a `Model` instance with key references to a dict """

    # sample person
    p = TestPerson(
      key=model.Key(TestPerson, 'john'), firstname='John', lastname='Doe')

    # john's cars
    bmw = TestCar(
      key=model.Key(TestCar, 'bmw'),
      make='BMW', model='M3', color='white', year=1998)
    civic = TestCar(
      key=model.Key(TestCar, 'civic'),
      make='Honda', model='Civic', color='black', year=2001)

    p.cars_ref = (bmw.key, civic.key)

    _john_raw = p.to_dict(convert_keys=False)  # without convert keys
    _john_converted = p.to_dict(convert_keys=True)  # with convert_keys

    assert bmw.key in _john_raw['cars_ref'], (
      "expected key for car `BMW` but found none"
      " in object: '%s'." % _john_raw)

    assert civic.key in _john_raw['cars_ref'], (
      "expected key for car `civic` but found none"
      " in object: '%s'." % _john_raw)

    assert bmw.key.urlsafe() in _john_converted['cars_ref'], (
      "expected converted key for car `BMW` but found none"
      " in object: '%s'." % _john_converted)

    assert civic.key.urlsafe() in _john_converted['cars_ref'], (
      "expected converted key for car `civic` but found none"
      " in object: '%s'." % _john_converted)

  def test_model_to_dict_convert_models(self):

    """ Test flattening a `Model` instance with submodels to a dict """

    # sample person
    p = TestPerson(
      key=model.Key(TestPerson, 'john'), firstname='John', lastname='Doe')

    # john's cars
    bmw = TestCar(
      key=model.Key(TestCar, 'bmw'),
      make='BMW', model='M3', color='white', year=1998)
    civic = TestCar(
      key=model.Key(TestCar, 'civic'),
      make='Honda', model='Civic', color='black', year=2001)

    p.cars_ref = (bmw.key, civic.key)
    p.cars_embedded = (bmw, civic)

    _john_raw = p.to_dict(convert_keys=False, convert_models=False)
    _john_converted = p.to_dict(convert_keys=True, convert_models=True)

    assert bmw in _john_raw['cars_embedded'], (
      "expected object for car `BMW` but found none"
      " in object: '%s'." % _john_raw)

    assert civic in _john_raw['cars_embedded'], (
      "expected object for car `civic` but found none"
      " in object: '%s'." % _john_raw)

    assert bmw.key in _john_raw['cars_ref'], (
      "expected key for car `BMW` but found none"
      " in object: '%s'." % _john_raw)

    assert civic.key in _john_raw['cars_ref'], (
      "expected key for car `civic` but found none"
      " in object: '%s'." % _john_raw)

    assert bmw.key.urlsafe() in _john_converted['cars_ref'], (
      "expected converted key for car `BMW` but found none"
      " in object: '%s'." % _john_converted)

    assert civic.key.urlsafe() in _john_converted['cars_ref'], (
      "expected converted key for car `civic` but found none"
      " in object: '%s'." % _john_converted)

    assert len(_john_converted['cars_embedded']) == 2
    for i in _john_converted['cars_embedded']:
      assert isinstance(i, dict), (
        "submodels are expected to convert to dicts"
        " when `convert_models` is active")

  def test_JSON_model_format(self):

    """ Test serializing a `Model` into a JSON struct """

    # sample person
    p = TestPerson(firstname='John', lastname='Doe')

    # prepare mini testsuite
    def test_json_flow(original, js=None):

      if not js:
        # execute for the caller
        original, js = original('to_dict'), original('to_json')

      # test string
      self.assertTrue(len(js) > 0)
      self.assertIsInstance(js, basestring)

      # test decode
      decoded = json.loads(js)
      self.assertIsInstance(decoded, dict)
      self.assertEqual(len(original), len(decoded))

      # test property values
      for key in original:
        self.assertEqual(original[key], decoded[key])

    # test regular to_json
    test_json_flow(p.to_dict(), p.to_json())

    # test all to_dict permutations with json
    test_structs = {
      'raw_dict': self.test_model_to_dict,
      'all_dict': self.test_model_to_dict_all_arguments,
      'mapped_dict': self.test_model_to_dict_with_map,
      'filtered_dict': self.test_model_to_dict_with_filter,
      'included_dict': self.test_model_to_dict_with_include,
      'excluded_dict': self.test_model_to_dict_with_exclude
    }

    # test each dict => json flow
    test_json_flow(test_structs['raw_dict'])
    test_json_flow(test_structs['all_dict'])
    test_json_flow(test_structs['mapped_dict'])
    test_json_flow(test_structs['filtered_dict'])
    test_json_flow(test_structs['included_dict'])
    test_json_flow(test_structs['excluded_dict'])

  def test_inflate_model_from_json(self):

    """ Test inflating a `Model` object from a JSON string """

    obj = {'firstname': 'John', 'lastname': 'Doe'}
    json_string = json.dumps(obj)

    # load into object
    p = TestPerson.from_json(json_string)
    assert p.firstname == 'John'
    assert p.lastname == 'Doe'

  with core.Library('msgpack') as (library, msgpack):

    import msgpack  # force re-import


    def test_msgpack_model_format(self):

      """ Test serializing a `Model` into a msgpack struct """

      # sample person
      p = TestPerson(firstname='John', lastname='Doe')

      # prepare mini testsuite
      def test_msgpack_flow(original, mp=None):

        if not mp:
          # execute for the caller
          original, mp = original('to_dict'), original('to_msgpack')

        # test string
        self.assertTrue(len(mp) > 0)
        self.assertIsInstance(mp, basestring)

        # test decode
        decoded = self.msgpack.unpackb(mp)
        self.assertIsInstance(decoded, dict)
        self.assertEqual(len(original), len(decoded))

        # test property values
        for key in original:
          self.assertEqual(original[key], decoded[key])

      # test regular to_msgpack
      test_msgpack_flow(p.to_dict(), p.to_msgpack())

      # test all to_dict permutations with msgpack
      test_structs = {
        'raw_dict': self.test_model_to_dict,
        'all_dict': self.test_model_to_dict_all_arguments,
        'mapped_dict': self.test_model_to_dict_with_map,
        'filtered_dict': self.test_model_to_dict_with_filter,
        'included_dict': self.test_model_to_dict_with_include,
        'excluded_dict': self.test_model_to_dict_with_exclude
      }

      # test each dict => msgpack flow
      test_msgpack_flow(test_structs['raw_dict'])
      test_msgpack_flow(test_structs['all_dict'])
      test_msgpack_flow(test_structs['mapped_dict'])
      test_msgpack_flow(test_structs['filtered_dict'])
      test_msgpack_flow(test_structs['included_dict'])
      test_msgpack_flow(test_structs['excluded_dict'])

    def test_inflate_model_from_msgpack(self):

      """ Test inflating a `Model` object from a msgpack payload """

      obj = {'firstname': 'John', 'lastname': 'Doe'}
      mpack = self.msgpack.dumps(obj)

      # load into object
      p = TestPerson.from_msgpack(mpack)
      assert p.firstname == 'John'
      assert p.lastname == 'Doe'

  def test_explicit(self):

    """ Test a `Model`'s behavior in `explicit` mode """

    # sample people
    s = TestPerson(firstname='Sam')
    p = TestPerson(firstname='John')

    # go into explicit mode
    self.assertEqual(p.__explicit__, False)
    explicit_firstname, explicit_lastname, explicit_active = None, None, None
    with p:
      explicit_firstname, explicit_lastname, explicit_active = (
          p.firstname, p.lastname, p.active)

      # only instances switch modes
      self.assertNotEqual(p.__explicit__, s.__explicit__)

      self.assertEqual(s.lastname, None)
      self.assertEqual(s.active, True)
      self.assertEqual(s.firstname, 'Sam')
      self.assertEqual(p.__explicit__, True)
    self.assertEqual(p.__explicit__, False)

    # test explicit values
    self.assertEqual(explicit_firstname, 'John')

    # default values are not returned in `explicit` mode
    self.assertEqual(explicit_active, datastructures.EMPTY)

    # unset properties are returned as EMPTY in `explicit` mode
    self.assertEqual(explicit_lastname, datastructures.EMPTY)

    # test implicit values
    self.assertEqual(p.firstname, 'John')
    self.assertEqual(p.lastname, None)
    self.assertEqual(p.active, True)

  def test_generator_implicit(self):

    """ Test a `Model`'s behavior when used as an iterator """

    # sample person
    p = TestPerson(firstname='John')

    # test implicit generator
    items = {}
    for name, value in p:
      items[name] = value

    self.assertEqual(len(items), 2)  # `active` should show up with default
    self.assertEqual(items['firstname'], 'John')
    self.assertEqual(items['active'], True)

  def test_generator_explicit(self):

    """ Test `Model` behavior when used as an iterator in `explicit` mode """

    # sample person
    p = TestPerson(firstname='John')

    # test explicit generator
    items = {}
    with p:
      for name, value in p:
        items[name] = value

    # should have _all_ properties
    self.assertEqual(len(items), len(p.__lookup__))
    self.assertEqual(items['firstname'], 'John')

    # defaults are returned as sentinels in `explicit` mode
    self.assertEqual(items['active'], datastructures.EMPTY)

    # unset properties are returned as sentinels in `explicit` mode
    self.assertEqual(items['lastname'], datastructures.EMPTY)

  def test_len(self):

    """ Test a `Model`'s behavior when used with `len()` """

    # sample person
    p = TestPerson()
    self.assertEqual(len(p), 0)

    # set 1st property
    p.firstname = 'John'
    self.assertEqual(len(p), 1)

    # set 2nd property
    p.lastname = 'Doe'
    self.assertEqual(len(p), 2)

  def test_nonzero(self):

    """ Test a `Model`'s falsyness with no properties """

    # sample peron
    p = TestPerson()
    self.assertTrue((not p))  # empty model should be falsy

    p.firstname = 'John'
    self.assertTrue(p)  # non-empty model is not falsy

  def test_get_invalid_property(self):

    """ Test getting an invalid `Model` property """

    # sample person
    p = TestPerson()

    # should be sealed off by `__slots__`
    with self.assertRaises(AttributeError):
      (p.blabble)

    # should be sealed off by metaclass-level `__slots__`
    with self.assertRaises(AttributeError):
      (TestPerson.blabble)

    # should be sealed off by good coding practices (lolz)
    with self.assertRaises(AttributeError):
      p._get_value('blabble')

  def test_get_value_all_properties(self):

    """ Test getting *all* properties via `_get_value` """

    # sample person
    p = TestPerson(firstname='John', lastname='Doe')
    properties = p._get_value(None)

    # should be a list of tuples
    self.assertEqual(len(properties), 6)
    self.assertIsInstance(properties, list)
    self.assertIsInstance(properties[0], tuple)

    # should retrieve even unset properties
    # (but they should be set to `None`, not the EMPTY sentinel of course)
    for k, v in properties:
      self.assertEqual(v, getattr(p, k))

  def test_model_getitem_setitem(self):

    """ Test a `Model`'s compliance with Python's Item API """

    # sample person
    p = TestPerson(firstname='John')

    # test __getitem__
    self.assertEqual(p.firstname, 'John')
    self.assertEqual(p['firstname'], 'John')

    # test __setitem__
    p['lastname'] = 'Gammon'
    self.assertEqual(p.lastname, 'Gammon')

    # try getting a nonexistent property, which should raise
    # `KeyError` instead of `AttributeError`
    with self.assertRaises(KeyError):
      (p['invalidproperty'])

    # make sure `AttributeError` still works properly
    with self.assertRaises(AttributeError):
      (p.invalidproperty)

  def test_model_setvalue(self):

    """ Test protected method `_set_value`, which is used by model internals """

    # sample person
    p = TestPerson(firstname='John')

    # try writing a new key
    x = p._set_value('key', model.VertexKey(TestPerson, "john"))
    self.assertEqual(x, p)

    # try writing to invalid property
    with self.assertRaises(AttributeError):
      p._set_value('invalidproperty', 'value')

    # quick test via descriptor API, which should also raise `AttributeError`
    with self.assertRaises(AttributeError):
      TestPerson.__dict__['firstname'].__set__(None, 'invalid')

  def test_model_setkey(self):

    """ Test protected method `_set_key`, which is used by model internals """

    # sample person
    p = TestPerson(firstname='John')

    # try writing an invalid key
    with self.assertRaises(TypeError):
      p._set_key(5.5)

    # try writing via kwargs
    k = model.VertexKey(TestPerson, "john")

    # try constructing via urlsafe
    p._set_key(urlsafe=k.urlsafe())

    # try constructing via raw
    p._set_key(raw=k.flatten(False)[1])

    # try already-constructed via kwargs
    p._set_key(constructed=k)

    # try providing both a value and formats, which should fail
    with self.assertRaises(TypeError):
      p._set_key(k, urlsafe=k.urlsafe())

    # try providing multiple formats, which should fail
    with self.assertRaises(TypeError):
      p._set_key(urlsafe=k.urlsafe(), raw=k.flatten(False)[1])

    # try passing nothing, which should fail
    with self.assertRaises(TypeError):
      p._set_key(None)

  def test_early_mutate(self):

    """ Test setting attributes and items on a model before it's ready """


    class EarlyMutateModel(model.Model):

      """ Tests mutation of properties before instantiation. """

      string = basestring

    # try writing to existing property
    with self.assertRaises(AttributeError):
      EarlyMutateModel.string = "testing123"

    # try writing a new property
    with self.assertRaises(AttributeError):
      EarlyMutateModel.newprop = "newvalue"

    # try writing to an internal property, which should work
    EarlyMutateModel.__impl__ = {}

  def test_validation_of_required_properties(self):

    """ Test validation of required properties """

    ## RequiredPropertyModel
    # Try validating properties marked as required.
    class RequiredPropertyModel(model.Model):

      """ Tests required properties. """

      nonrequired = basestring
      required = basestring, {'required': True}

    # sample model
    p = RequiredPropertyModel(nonrequired='sup')

    # try putting, should raise `ValueError`
    with self.assertRaises(ValueError):
      p.put()

    # should not raise errors
    p.required = 'sup'
    p.put()

  def test_validation_of_property_basetype(self):

    """ Test validation of property basetypes """

    ## BasetypedPropertyModel
    # Try validating properties by basetype.
    class BasetypedPropertyModel(model.Model):

      """ Tests property basetypes. """

      string = basestring
      number = int
      floating = float
      boolean = bool
      always_empty = basestring

    # sample model
    b = BasetypedPropertyModel()

    # test strings
    b.string = 5
    with self.assertRaises(ValueError):
      b.put()
    b.string = 'sample'

    # test integers
    b.number = '5'
    with self.assertRaises(ValueError):
      b.put()
    b.number = 5

    # test floats
    b.floating = 5
    with self.assertRaises(ValueError):
      b.put()
    b.floating = 5.5

    # test booleans
    b.boolean = 5.5
    with self.assertRaises(ValueError):
      b.put()
    b.boolean = True

    # should not except
    b.put()

  def test_validation_of_repeated_properties(self):

    """ Test validation of repeated properties """

    ## RepeatedPropertyModel
    # Try validating properties marked as repeated.
    class RepeatedPropertyModel(model.Model):

      """ Tests repeated properties. """

      nonrepeated = basestring
      repeated = int, {'repeated': True}

    # sample model
    r = RepeatedPropertyModel(nonrepeated=['blabble', '1', '2', '3'])

    # try repeated value in nonrepeated property
    with self.assertRaises(ValueError):
      r.put()

    # set to valid value
    r.nonrepeated = 'validvalue'

    # try nonrepeated value in repeated property
    r.repeated = 5
    with self.assertRaises(ValueError):
      r.put()

    # try invalid basetype in proper repeated field
    r.repeated = ['one', 'two', 'three']
    with self.assertRaises(ValueError):
      r.put()

    # set to valid value and put, should not except
    r.repeated = [1, 2, 3]
    r.put()

  def test_class_level_default_value(self):

    """ Test reading a property with a default set at the class level """

    ## ClassDefaultSample
    # Try grabbing the value of a defaulted property at the class level.
    class ClassDefaultSample(model.Model):

      """ Tests properties with default values at the class level. """

      sample_default = basestring, {'default': 'Hello, default!'}

    # try on the class level
    self.assertIsInstance(ClassDefaultSample.sample_default, model.Property)

  def test_class_level_propery_access(self):

    """ Test class-level property access on `Model` subclasses """

    assert isinstance(TestCar.make, model.Property)
    assert 'make' in TestCar.make.__repr__()
    assert 'Property' in TestCar.make.__repr__()

  def test_class_level_item_access(self):

    """ Test class-level item access on `Model` subclasses """

    assert isinstance(TestCar['make'], model.Property)
    assert 'make' in TestCar['make'].__repr__()
    assert 'Property' in TestCar['make'].__repr__()

  def test_graph_class_existence(self):

    """ Test proper export of ``Vertex`` and ``Edge`` models """

    assert hasattr(model, 'Vertex')
    assert hasattr(model, 'Edge')
    assert issubclass(model.Vertex, model.Model)
    assert issubclass(model.Edge, model.Model)

  def test_vertex_class_mro(self):

    """ Test proper MRO for ``Vertex`` models """

    assert hasattr(TestPerson, 'edges')
    assert hasattr(TestPerson(), 'edges')
    assert hasattr(TestPerson, 'neighbors')
    assert hasattr(TestPerson(), 'neighbors')
    assert issubclass(TestPerson, model.Vertex)
    assert isinstance(TestPerson(), model.Vertex)

  def test_edge_class_mro(self):

    """ Test proper MRO for ``Edge`` models """

    assert hasattr(Friendship, 'peers')
    assert issubclass(Friendship, model.Edge)
