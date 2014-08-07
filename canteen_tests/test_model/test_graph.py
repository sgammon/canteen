# -*- coding: utf-8 -*-

'''

  graph model tests
  ~~~~~~~~~~~~~~~~~

  tests graph-extended models.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# canteen model API
from canteen import model
from canteen.test import FrameworkTest


class Person(model.Vertex):

  ''' sample person (also a vertex) '''

  firstname = basestring
  lastname = basestring


class Friendship(model.Edge):

  ''' sample friendship (edge that connects two people) '''

  year_met = int


class VertexModelTests(FrameworkTest):

  ''' Tests `model.Vertex`. '''

  subject = None

  def test_construct(self):

    ''' Test constructing a `Vertex` model '''

    return Person(
        key=model.Key(Person, 'sup'),
        firstname='John',
        lastname='Doe')

  def test_vertex_put(self):

    ''' Test saving a `Vertex` model to storage '''

    return self.test_construct().put(adapter=self.subject)

  def test_vertex_get(self):

    ''' Test retrieving a `Vertex` by its key '''

    assert Person.get(self.test_vertex_put(), adapter=self.subject)


class EdgeModelTests(FrameworkTest):

  ''' Tests `model.Edge`. '''

  subject = None

  def test_construct(self):

    ''' Test constructing an `Edge` model '''

    # sam + alex
    sam, alex = Person(firstname='Sam'), Person(firstname='Alex')

    # low-level edge construct
    sam_to_alex = Friendship(sam, alex,
                              key=model.Key(Friendship, 'sup'),
                              year_met=2003)

    return sam_to_alex

  def test_edge_put(self):

    ''' Test saving an `Edge` model to storage '''

    return self.test_construct().put(adapter=self.subject)

  def test_edge_get(self):

    ''' Test retrieving an `Edge` by its key '''

    assert Friendship.get(self.test_edge_put(), adapter=self.subject)
