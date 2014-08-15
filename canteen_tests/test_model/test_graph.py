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

# default inmemory adapter
from canteen.model.adapter import inmemory


class Person(model.Vertex):

  ''' sample person (also a vertex) '''

  firstname = basestring
  lastname = basestring


class Teammates(model.Edge):

  ''' sample teammate-ship (edge that connects two people) '''

  year_met = int


class VertexModelTests(FrameworkTest):

  ''' Tests `model.Vertex`. '''

  subject = inmemory.InMemoryAdapter()

  def test_construct(self):

    ''' Test constructing a `Vertex` model '''

    return Person(
        key=model.VertexKey(Person, 'sup'),
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

  subject = inmemory.InMemoryAdapter()

  def test_construct_undirected(self):

    ''' Test constructing an undirected `Edge` model '''

    # sam + alex
    sam, alex = Person(firstname='Sam'), Person(firstname='Alex')

    # low-level edge construct
    sam_to_alex = Teammates((sam, alex),
                            key=model.EdgeKey(Teammates, 'sup'),
                            year_met=2003)

    return sam_to_alex

  def test_construct_directed(self):

    ''' Test constructing a directed `Edge` model '''

    # ian + david
    ian, david = Person(firstname='Sam'), Person(firstname='Alex')

    # low-level edge construct
    ian_to_david = Teammates(ian, david,
                              key=model.EdgeKey(Teammates, 'sup'),
                              year_met=2003)

    return ian_to_david

  def test_undirected_edge_put(self):

    ''' Test saving an undirected `Edge` model '''

    return self.test_construct_undirected().put(adapter=self.subject)

  def test_directed_edge_put(self):

    ''' Test saving a directed `Edge` model '''

    return self.test_construct_directed().put(adapter=self.subject)

  def test_undirected_edge_get(self):

    ''' Test retrieving an undirected `Edge` by its key '''

    assert Teammates.get(self.test_undirected_edge_put(), adapter=self.subject)

  def test_directed_edge_get(self):

    ''' Test retrieving a directed `Edge` by its key '''

    assert Teammates.get(self.test_directed_edge_put(), adapter=self.subject)
