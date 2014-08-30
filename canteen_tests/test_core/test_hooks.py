# -*- coding: utf-8 -*-

"""

  core hook tests
  ~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# testing
from canteen import test

# hook and runtime subsystems
from canteen.core import hooks


class HookResponderTests(test.FrameworkTest):

  """ Tests ``hooks.HookResponder``, which allows the
      framework or downstream developers to execute
      code at discrete, named points in Canteen's
      execution flow. """

  def test_construct(self):

    """ Test simple construction of a `HookResponder` """

    r = hooks.HookResponder('sample-event')
    assert 'sample-event' in r.__hooks__

    r = hooks.HookResponder('sample-event', 'sample-event-2')
    assert 'sample-event' in r.__hooks__
    assert 'sample-event-2' in r.__hooks__

    r = hooks.HookResponder('sample-event', 'sample-event-2', rollup=True)
    assert 'sample-event' in r.__hooks__
    assert 'sample-event-2' in r.__hooks__
    assert r.__argspec__.__rollup__ is True

    r = hooks.HookResponder('sample-event', 'sample-event-2', rollup=False,
                                                              notify=True)
    assert 'sample-event' in r.__hooks__
    assert 'sample-event-2' in r.__hooks__
    assert r.__argspec__.__rollup__ is False
    assert r.__argspec__.__notify__ is True

    return r

  def test_implied_argspec(self):

    """ Test binding `Context` with an implied argspec """

    def responder(item_one):

      """ implied responder, satisfied using inspection """

      # i don't do anything
      assert item_one == 5
      return item_one

    r = hooks.HookResponder('test_event')(responder)

    # try executing
    r('test_event', item_one=5)

  def test_bind_context(self):

    """ Test binding `Context` for a `HookResponder` """

    c = hooks.Context(('sample_item', 'sample_item2'))

    def sup(*args, **kwargs): return kwargs

    # bind context
    unwrapped = c(sup)
    assert 'sample_item' in c.__requested__
    assert 'sample_item2' in c.__requested__
    assert c.__rollup__ is True
    assert c.__notify__ is False
    assert callable(unwrapped)

    result = unwrapped('sample-event', sample_item=True, sample_item2=False,
                                                         yompin=True)
    assert 'sample_item' in result and result['sample_item'] is True
    assert 'sample_item2' in result and result['sample_item2'] is False

  def test_bind_invalid_context(self):

    """ Test invalid binding behavior for `Context` """

    c = hooks.Context(('sample_item', 'sample_item2', 'sample_item3'))

    def sup(*args, **kwargs): return kwargs

    # bind context
    unwrapped = c(sup)
    assert 'sample_item' in c.__requested__
    assert 'sample_item2' in c.__requested__
    assert c.__rollup__ is True
    assert c.__notify__ is False
    assert callable(unwrapped)

    with self.assertRaises(RuntimeError):
      unwrapped('sample-event', sample_item=True, sample_item2=False,
                                                  yompin=True)
