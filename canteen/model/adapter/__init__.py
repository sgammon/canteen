# -*- coding: utf-8 -*-

"""

  model adapters
  ~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# module constants
__version__ = (0, 8)  # module version-string
__doc__ = "Contains modules that adapt models to various storage backends."


# abstract adapters
from . import abstract
from .abstract import Mixin
from .abstract import KeyMixin
from .abstract import ModelMixin
from .abstract import VertexMixin
from .abstract import EdgeMixin
from .abstract import ModelAdapter
from .abstract import IndexedModelAdapter

abstract_adapters = [abstract, ModelAdapter, IndexedModelAdapter]


# adapter modules
from . import redis
from . import inmemory
from . import protorpc

modules = [inmemory, protorpc, redis]


# concrete adapters
from .redis import RedisAdapter
from .inmemory import InMemoryAdapter

concrete = [InMemoryAdapter, RedisAdapter]


# builtin mixins
from . import core
from .core import DictMixin
from .core import JSONMixin

base_mixins = [KeyMixin, ModelMixin, VertexMixin, EdgeMixin]
builtin_mixins = [DictMixin, JSONMixin]


__adapters__ = tuple((
  abstract_adapters +
  modules +
  concrete +
  builtin_mixins +
  base_mixins))
