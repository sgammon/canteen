# -*- coding: utf-8 -*-

'''

'''

# 3rd party / stdlib
try:
  import logbook as logging
except ImportError:
  import logging

Logger = logging.Logger


__all__ = ('Logger',)
