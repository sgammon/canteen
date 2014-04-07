# -*- coding: utf-8 -*-

'''

  canteen: realtime logic
  ~~~~~~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# core and utils
from ..base import logic
from ..util import decorators


@decorators.bind('realtime', namespace=True)
class RealtimeSemantics(logic.Logic):

  '''  '''

  def on_connect(self, client):

  	'''  '''

  	pass

  def on_message(self, client, message):

  	'''  '''

  	pass


__all__ = ('RealtimeSemantics',)
