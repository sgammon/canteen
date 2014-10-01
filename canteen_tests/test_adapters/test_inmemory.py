# -*- coding: utf-8 -*-

"""

  inmemory adapter tests
  ~~~~~~~~~~~~~~~~~~~~~~

  tests canteen's builtin inmemory DB engine.

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
      A copy of this license is included as ``LICENSE.md`` in
      the root of the project.

"""

# canteen model API
from canteen.model.adapter import inmemory

# abstract test bases
from .test_abstract import DirectedGraphAdapterTests


class InMemoryAdapterTests(DirectedGraphAdapterTests):

  """ Tests `model.adapter.inmemory` """

  __abstract__ = False
  subject = inmemory.InMemoryAdapter
