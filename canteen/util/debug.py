# -*- coding: utf-8 -*-

'''

'''

# 3rd party / stdlib
try:
  import logbook as logging
except ImportError:
  import logging


def Logger(name):

  '''  '''

  logger = logging.getLogger(name)
  logger.setLevel(10)
  return logger


__all__ = ('Logger',)
