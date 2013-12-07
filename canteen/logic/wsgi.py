# -*- coding: utf-8 -*-

'''

  canteen WSGI logic
  ~~~~~~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# base logic & utils
from ..base import logic
from ..util import decorators


@decorators.bind('wsgi', namespace=False)
class WSGI(logic.Logic):

	'''  '''

	@decorators.bind('dispatch')
	def __call__(self, environ, start_response):

		'''  '''

		import pdb; pdb.set_trace()
		return None
