# -*- coding: utf-8 -*-

'''

'''

# stdlib
import sys

# 3rd party / stdlib
try:
  import logbook as logging
except ImportError:
  import logging
  logging.basicConfig(stream=sys.stdout, level=10, format='%(message)s')


def Logger(name):

  '''  '''

  logger = logging.getLogger(name)
  logger.setLevel(10)
  return logger


__all__ = ('Logger',)
