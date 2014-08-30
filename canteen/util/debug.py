# -*- coding: utf-8 -*-

"""

  debug utils
  ~~~~~~~~~~~

  :author: Sam Gammon <sg@samgammon.com>
  :copyright: (c) Sam Gammon, 2014
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

"""

# stdlib
import sys

# 3rd party / stdlib
try:
  # noinspection PyPackageRequirements
  import logbook as logging
except ImportError:
  import logging
  logging.basicConfig(stream=sys.stdout, level=10, format='%(message)s')


def Logger(name):  # pragma: no cover

  """  """

  logger = logging.getLogger(name)
  logger.setLevel(10)
  return logger
