# -*- coding: utf-8 -*-

'''

  canteen model tests
  ~~~~~~~~~~~~~~~~~~~

  tests canteen's model classes.

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this library is included as ``LICENSE.md`` in
            the root of the project.

'''

# stdlib
import abc
import json
import inspect

# appconfig
try:
    import config; _APPCONFIG = True
except ImportError as e:  # pragma: no cover
    _APPCONFIG = False
else:
    # set debug mode for all model-related stuff
    config.config['apptools.model']['debug'] = True
    for k in filter(lambda x: x.startswith('apptools.model'), config.config.iterkeys()):
        config.config[k]['debug'] = True

# canteen model API
from canteen import model
from canteen.model import adapter
from canteen.model import exceptions

# canteen tests
from canteen.test import FrameworkTest

# canteen utils
from canteen.util import struct as datastructures


## == Test Models == ##

## Car
# Simple model simulating a car.
class Car(model.Model):

    ''' An automobile. '''

    make = basestring, {'indexed': True}
    model = basestring, {'indexed': True}
    year = int, {'choices': xrange(1900, 2015)}
    color = basestring, {'choices': ('blue', 'green', 'red', 'silver', 'white', 'black')}


## Person
# Simple model simulating a person.
class Person(model.Model):

    ''' A human being. '''

    firstname = basestring, {'indexed': True}
    lastname = basestring, {'indexed': True}
    active = bool, {'default': True}
    cars = Car, {'repeated': True}


## ModelTests
class ModelTests(FrameworkTest):

    ''' Tests `model.Model` and `model.AbstractModel`. '''

    def test_construct_model(self):

        ''' Try constructing a Model manually. '''

        # construct our car record
        car = Car(make='BMW', model='M3', year=2013, color='white')

        # construct our person record
        person = Person()
        person.firstname = 'John'
        person.cars = [car]

        # perform tests
        self.assertIsInstance(car, Car)
        self.assertIsInstance(person, Person)
        self.assertEqual(person.firstname, 'John')
        self.assertIsInstance(person.cars, list)
        self.assertEqual(len(person.cars), 1)
        self.assertIsInstance(person.cars[0], Car)

        # test defaults
        self.assertEqual(person.active, True)

        # test unsets
        self.assertEqual(person.lastname, None)

        # test __repr__
        cls = str(Person)
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

        ''' Try an invalid model adapter, which should raise `RuntimeError`. '''

        with self.assertRaises(RuntimeError):

            ## InvalidAdapterModel
            # Tests an invalid, but explicitly listed, model adapter.
            class InvalidAdapterModel(model.Model):

                __adapter__ = 'DumbInvalidModelAdapter'

                prop1 = basestring

    def test_model_inheritance(self):

        ''' Make sure there's a proper inheritance structure for `model.Model`. '''

        self.assertTrue(issubclass(Car, model.Model))
        self.assertTrue(issubclass(Person, model.Model))
        self.assertTrue(issubclass(model.Model, model.AbstractModel))

    def test_model_schema(self):

        ''' Make sure there's a proper schema spec on `model.Model`. '''

        # check lookup
        self.assertTrue(hasattr(Person, '__lookup__'))
        self.assertIsInstance(Person.__lookup__, frozenset)

        # check property descriptors
        self.assertTrue(hasattr(Person, 'firstname'))
        self.assertTrue(hasattr(Person, 'lastname'))
        self.assertTrue(hasattr(Person, 'cars'))

        # check kind
        self.assertTrue(hasattr(Person, 'kind'))
        self.assertIsInstance(Person.kind(), basestring)

        # check set/get
        self.assertTrue(hasattr(Person, '_get_value'))
        self.assertTrue(hasattr(Person, '_set_value'))
        self.assertTrue(inspect.ismethod(Person._get_value))
        self.assertTrue(inspect.ismethod(Person._set_value))

        # check key
        self.assertTrue(hasattr(Person, 'key'))
        self.assertTrue((not hasattr(Person, '__key__')))  # should not have key until instantiation
        self.assertTrue(hasattr(Person(), '__key__'))

    def test_model_set_attribute(self):

        ''' Try setting an unknown and known attribute. '''

        # try construction assignment
        john = Person(firstname='John')
        self.assertEqual(john.firstname, 'John')

        # re-assign
        john.firstname = 'Blabs'
        self.assertEqual(john.firstname, 'Blabs')

        # try assigning missing property
        with self.assertRaises(AttributeError):
            john.blabs = 'John'

    def test_model_adapter(self):

        ''' Make sure the adapter is attached correctly to `model.Model`. '''

        # make sure it's on the classlevel
        self.assertTrue(hasattr(Person, '__adapter__'))
        self.assertIsInstance(Person.__adapter__, adapter.ModelAdapter)

    def test_model_stringify(self):

        ''' Test the string representation of a Model object. '''

        self.assertIsInstance(Person().__repr__(), basestring)

    def test_model_kind(self):

        ''' Make sure the `Model.kind` is properly set. '''

        # test class-level kind
        self.assertIsInstance(Person.kind(), basestring)
        self.assertEqual(Person.kind(), "Person")

        # test object-level kind
        john = Person()
        self.assertIsInstance(john.kind(), basestring)
        self.assertEqual(john.kind(), "Person")

    def test_abstract_model(self):

        ''' Make sure `model.AbstractModel` works abstractly. '''

        # make sure it's ABC-enabled
        self.assertTrue((not isinstance(model.Model, abc.ABCMeta)))

        # try directly-instantiation
        with self.assertRaises(exceptions.AbstractConstructionFailure):
            (model.AbstractModel())

    def test_concrete_model(self):

        ''' Make sure `model.Model` works concretely. '''

        ## test simple construction
        self.assertIsInstance(Person(), Person)

        ## SampleModel
        # Test parent model class.
        class SampleModel(model.Model):

            ''' Test parent model class. '''

            parent = basestring

        ## SampleSubModel
        # Test child model class.
        class SampleSubModel(SampleModel):

            ''' Test child model class. '''

            child = basestring

        ## test properties
        self.assertTrue(hasattr(SampleModel, 'parent'))
        self.assertTrue((not hasattr(SampleModel, 'child')))

        ## test submodel properties
        self.assertTrue(hasattr(SampleSubModel, 'child'))
        self.assertTrue(hasattr(SampleSubModel, 'parent'))

        ## test recursive subclassing
        self.assertIsInstance(SampleModel(), model.Model)
        self.assertIsInstance(SampleSubModel(), SampleModel)
        self.assertIsInstance(SampleSubModel(), model.Model)

    def test_model_to_dict(self, method='to_dict'):

        ''' Try flattening a Model into a raw dictionary. '''

        # sample person
        p = Person(firstname='John')
        raw_dict = getattr(p, method)()

        if method == 'to_dict':
            # try regular to_dict
            self.assertEqual(len(raw_dict), 2)
            self.assertIsInstance(raw_dict, dict)
            self.assertEqual(raw_dict['firstname'], 'John')  # we set this explicitly
            self.assertEqual(raw_dict['active'], True)  # this is defaulted, should export

            with self.assertRaises(KeyError):
                raw_dict['lastname']
        return raw_dict

    def test_model_to_dict_all_arguments(self, method='to_dict'):

        ''' Try using `Model.to_dict` with the `all` flag. '''

        # sample person
        p = Person(firstname='John')
        all_dict = getattr(p, method)(_all=True)

        if method == 'to_dict':
            # test dict with `all`
            self.assertEqual(len(all_dict), len(p.__lookup__))
            self.assertEqual(all_dict['firstname'], 'John')
            self.assertEqual(all_dict['lastname'], None)
            self.assertEqual(all_dict['active'], True)
        return all_dict

    def test_model_to_dict_with_filter(self, method='to_dict'):

        ''' Try using `Model.to_dict` with a filter function. '''

        # sample person
        p = Person(firstname='John')
        filtered_dict = getattr(p, method)(filter=lambda x: len(x[0]) > 7)  # should filter out 'active'

        if method == 'to_dict':
            # test filter
            self.assertEqual(len(filtered_dict), 1)
            self.assertIsInstance(filtered_dict, dict)
            self.assertEqual(filtered_dict['firstname'], 'John')

            with self.assertRaises(KeyError):
                filtered_dict['active']
        return filtered_dict

    def test_model_to_dict_with_include(self, method='to_dict'):

        ''' Try using `Model.to_dict` with an inclusion list. '''

        # sample person
        p = Person(firstname='John')
        included_dict = getattr(p, method)(include=('firstname', 'lastname'))

        if method == 'to_dict':
            # test include
            self.assertEqual(len(included_dict), 2)  # should still include `lastname` as 'None'
            self.assertIsInstance(included_dict, dict)
            self.assertEqual(included_dict['firstname'], 'John')
            self.assertEqual(included_dict['lastname'], None)

            with self.assertRaises(KeyError):
                included_dict['active']  # should not include `active`
        return included_dict

    def test_model_to_dict_with_exclude(self, method='to_dict'):

        ''' Try using `Model.to_dict` with an exclusion list. '''

        # sample person
        p = Person(firstname='John')
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

        ''' Try using `Model.to_dict` with a map function. '''

        # sample person
        p = Person(firstname='John')
        mapped_dict = getattr(p, method)(map=lambda x: tuple([x[0] + '-cool', x[1]]))

        if method == 'to_dict':
            # test map
            self.assertEqual(len(mapped_dict), 2)
            self.assertIsInstance(mapped_dict, dict)
            self.assertEqual(mapped_dict['firstname-cool'], 'John')
            self.assertEqual(mapped_dict['active-cool'], True)
        return mapped_dict

    def test_JSON_model_format(self):

        ''' Try serializing a Model into a JSON struct. '''

        # sample person
        p = Person(firstname='John', lastname='Doe')

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

    def test_explicit(self):

        ''' Test a Model's behavior in `explicit` mode. '''

        # sample people
        s = Person(firstname='Sam')
        p = Person(firstname='John')

        # go into explicit mode
        self.assertEqual(p.__explicit__, False)
        explicit_firstname, explicit_lastname, explicit_active = None, None, None
        with p:
            explicit_firstname, explicit_lastname, explicit_active = p.firstname, p.lastname, p.active
            self.assertNotEqual(p.__explicit__, s.__explicit__)  # only instances switch modes

            self.assertEqual(s.lastname, None)
            self.assertEqual(s.active, True)
            self.assertEqual(s.firstname, 'Sam')
            self.assertEqual(p.__explicit__, True)
        self.assertEqual(p.__explicit__, False)

        # test explicit values
        self.assertEqual(explicit_firstname, 'John')
        self.assertEqual(explicit_active, datastructures._EMPTY)  # default values are not returned in `explicit` mode
        self.assertEqual(explicit_lastname, datastructures._EMPTY)  # unset properties are returned as _EMPTY in `explicit` mode

        # test implicit values
        self.assertEqual(p.firstname, 'John')
        self.assertEqual(p.lastname, None)
        self.assertEqual(p.active, True)

    def test_generator_implicit(self):

        ''' Test a Model's behavior when used as an iterator. '''

        # sample person
        p = Person(firstname='John')

        # test implicit generator
        items = {}
        for name, value in p:
            items[name] = value

        self.assertEqual(len(items), 2)  # `active` should show up with default
        self.assertEqual(items['firstname'], 'John')
        self.assertEqual(items['active'], True)

    def test_generator_explicit(self):

        ''' Test a Model's behavior when used as an iterator in `explicit` mode. '''

        # sample person
        p = Person(firstname='John')

        # test explicit generator
        items = {}
        with p:
            for name, value in p:
                items[name] = value

        self.assertEqual(len(items), len(p.__lookup__))  # should have _all_ properties
        self.assertEqual(items['firstname'], 'John')
        self.assertEqual(items['active'], datastructures._EMPTY)  # defaults are returned as sentinels in `explicit` mode
        self.assertEqual(items['lastname'], datastructures._EMPTY)  # unset properties are returned as sentinels in `explicit` mode

    def test_len(self):

        ''' Test a Model's behavior when used with `len()`. '''

        # sample person
        p = Person()
        self.assertEqual(len(p), 0)

        # set 1st property
        p.firstname = 'John'
        self.assertEqual(len(p), 1)

        # set 2nd property
        p.lastname = 'Doe'
        self.assertEqual(len(p), 2)

    def test_nonzero(self):

        ''' Test a Model's falsyness with no properties. '''

        # sample peron
        p = Person()
        self.assertTrue((not p))  # empty model should be falsy

        p.firstname = 'John'
        self.assertTrue(p)  # non-empty model is not falsy

    def test_get_invalid_property(self):

        ''' Try getting an invalid model property. '''

        # sample person
        p = Person()

        # should be sealed off by `__slots__`
        with self.assertRaises(AttributeError):
            (p.blabble)

        # should be sealed off by metaclass-level `__slots__`
        with self.assertRaises(AttributeError):
            (Person.blabble)

        # should be sealed off by good coding practices (lolz)
        with self.assertRaises(AttributeError):
            p._get_value('blabble')

    def test_get_value_all_properties(self):

        ''' Try getting *all* properties via `_get_value`. '''

        # sample person
        p = Person(firstname='John', lastname='Doe')
        properties = p._get_value(None)

        # should be a list of tuples
        self.assertEqual(len(properties), 4)
        self.assertIsInstance(properties, list)
        self.assertIsInstance(properties[0], tuple)

        # should retrieve even unset properties (but they should be set to `None`, not the _EMPTY sentinel of course)
        for k, v in properties:
            self.assertEqual(v, getattr(p, k))

    def test_model_getitem_setitem(self):

        ''' Test a model's compliance with Python's Item API. '''

        # sample person
        p = Person(firstname='John')

        # test __getitem__
        self.assertEqual(p.firstname, 'John')
        self.assertEqual(p['firstname'], 'John')

        # test __setitem__
        p['lastname'] = 'Gammon'
        self.assertEqual(p.lastname, 'Gammon')

        # try getting a nonexistent property, which should raise `KeyError` instead of `AttributeError`
        with self.assertRaises(KeyError):
            (p['invalidproperty'])

        # make sure `AttributeError` still works properly
        with self.assertRaises(AttributeError):
            (p.invalidproperty)

    def test_model_setvalue(self):

        ''' Test the protected method `_set_value`, which is used by Model API internals. '''

        # sample person
        p = Person(firstname='John')

        # try writing a new key
        x = p._set_value('key', model.Key(Person, "john"))
        self.assertEqual(x, p)

        # try writing to invalid property
        with self.assertRaises(AttributeError):
            p._set_value('invalidproperty', 'value')

        # quick test via descriptor API, which should also raise `AttributeError`
        with self.assertRaises(AttributeError):
            Person.__dict__['firstname'].__set__(None, 'invalid')

    def test_model_setkey(self):

        ''' Test the protected method `_set_key`, which is used by Model API internals. '''

        # sample person
        p = Person(firstname='John')

        # try writing an invalid key
        with self.assertRaises(TypeError):
            p._set_key(5.5)

        # try writing via kwargs
        k = model.Key(Person, "john")

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

        ''' Try setting attributes and items on a model before it's ready (i.e. before instantiation). '''

        ## EarlyMutateModel
        # Tests mutation of properties before instantiation, which should fail.
        class EarlyMutateModel(model.Model):

            ''' Tests mutation of properties before instantiation. '''

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

        ''' Try testing validation of required property. '''

        ## RequiredPropertyModel
        # Try validating properties marked as required.
        class RequiredPropertyModel(model.Model):

            ''' Tests required properties. '''

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

        ''' Try testing validation of property basetypes. '''

        ## BasetypedPropertyModel
        # Try validating properties by basetype.
        class BasetypedPropertyModel(model.Model):

            ''' Tests property basetypes. '''

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

        ''' Try testing validation of repeated properties. '''

        ## RepeatedPropertyModel
        # Try validating properties marked as repeated.
        class RepeatedPropertyModel(model.Model):

            ''' Tests repeated properties. '''

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

        ''' Try grabbing the value of a property with a default set at the class level. '''

        ## ClassDefaultSample
        # Try grabbing the value of a defaulted property at the class level.
        class ClassDefaultSample(model.Model):

            ''' Tests properties with default values at the class level. '''

            sample_default = basestring, {'default': 'Hello, default!'}

        # try on the class level
        self.assertIsInstance(ClassDefaultSample.sample_default, model.Property)
