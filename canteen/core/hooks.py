# -*- coding: utf-8 -*-

'''

'''

# stdlib
import inspect

# core runtime
from . import runtime


class HookResponder(object):

  '''  '''

  __slots__ = (
    '__func__',  # inner function
    '__wrap__',  # hook wrapper
    '__hooks__',  # event names to fire on
    '__argspec__'  # argspec (explicit or implied)
  )

  def __init__(self, *events, **kwargs):

    '''  '''

    self.__hooks__, self.__argspec__, self.__wrap__ = (
      frozenset(events),  # events to fire on
      Context(
        kwargs.get('context'),  # explicit argspec
        kwargs.get('rollup', False)  # kwargs flag
      ) if ('context' in kwargs or 'rollup' in kwargs) else None,
      kwargs.get('wrap')  # function to wrap the hook in, if any
    )

  def __register__(self, context):

    '''  '''

    for i in self.__hooks__:  # add hook for each event name
      runtime.Runtime.add_hook(i, (context, self))

  def __call__(self, *args, **kwargs):

    '''  '''

    if not hasattr(self, '__func__') or not getattr(self, '__func__'):
      # if there's no explicit argspec, inspect
      hook = args[0]
      _hook_i = inspect.getargspec(hook)
      self.__argspec__ = self.__argspec__ or Context([i for i in _hook_i.args if i != 'self'], _hook_i.keywords is not None)

      def run_hook(*args, **kwargs):

        '''  '''

        if self.__wrap__:
          return self.__argspec__(self.__wrap__(hook))(*args, **kwargs)
        return self.__argspec__(hook)(*args, **kwargs)

      return setattr(self, '__func__', run_hook) or self  # mount run_hook

    return self.__func__(*args, **kwargs)


class Context(object):

  '''  '''

  __slots__ = (
    '__requested__',  # requested args
    '__rollup__'  # acceptance of kwargs
  )

  def __init__(self, requested, rollup=True):

    '''  '''

    self.__requested__, self.__rollup__ = (
      requested, rollup
    )

  def __call__(self, func):

    '''  '''

    if func is object:
      import pdb; pdb.set_trace()

    def with_context(*args, **context):

      '''  '''

      # calculate materialized args
      _args, _kwargs = [], {}
      if self.__requested__:
        for prop in self.__requested__:
          if prop not in context:
            continue
          _args.append(context[prop])

      # honor kwargs
      if self.__rollup__: _kwargs = context

      # dispatch!
      if func is object:
        import pdb; pdb.set_trace()
      return (func if not isinstance(func, (classmethod, staticmethod)) else func.__func__)(*tuple(list(args) + _args), **_kwargs)

    return with_context
