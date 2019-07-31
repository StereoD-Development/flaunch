"""
Logging utility for the build routines
"""
from __future__ import absolute_import

import sys
import logging

from contextlib import contextmanager

# -- Defaults and Globals
MESSAGE_FORMAT = '[%(asctime)s - %(levelname)s!tabme!]: {}%(message)s'
DATETIME_FORMAT = '%d/%m/%Y %I:%M:%S %p'
DEFAULT_HANDLER = None
FILE_HANDLER = None

CURRENT_INDENT = 0

class FLaunchFormater(logging.Formatter):

    def format(self, record):
        s = super(FLaunchFormater, self).format(record)
        idx = s.index('!tabme!')
        s = s.replace('!tabme!', ' ' * (31 - idx))
        return s

DEFAULT_FORMAT = FLaunchFormater(
    fmt=MESSAGE_FORMAT.format(''),
    datefmt=DATETIME_FORMAT
)


def start(verbose, output_file=None):
    """
    Initialize logging based on the verbosity. Augment the message
    format.
    :param verbose: bool, turn chatty things on
    :return: None
    """
    global DEFAULT_HANDLER
    global FILE_HANDLER
    global DEFAULT_FORMAT

    level = logging.INFO if not verbose else logging.DEBUG

    logger = logging.getLogger()
    logger.setLevel(level)

    DEFAULT_HANDLER = logging.StreamHandler()
    logger.addHandler(DEFAULT_HANDLER)

    if output_file:
        FILE_HANDLER = logging.FileHandler(filename=output_file)
        logger.addHandler(FILE_HANDLER)

    DEFAULT_HANDLER.setFormatter(DEFAULT_FORMAT)


@contextmanager
def log_indent():
    """
    Indent the messages using a with statemment
    """
    global DEFAULT_HANDLER
    global FILE_HANDLER
    global CURRENT_INDENT

    CURRENT_INDENT += 4
    indented_format = FLaunchFormater(
        fmt=MESSAGE_FORMAT.format(' '*CURRENT_INDENT),
        datefmt=DATETIME_FORMAT
    )
    DEFAULT_HANDLER.setFormatter(indented_format)
    if FILE_HANDLER is not None:
        FILE_HANDLER.setFormatter(indented_format)

    yield
    CURRENT_INDENT -= 4
    right_format = FLaunchFormater(
        fmt=MESSAGE_FORMAT.format(' '*CURRENT_INDENT),
        datefmt=DATETIME_FORMAT
    )
    DEFAULT_HANDLER.setFormatter(right_format)
    if FILE_HANDLER is not None:
        FILE_HANDLER.setFormatter(right_format)

