"""Tests for the logging verbosity setup."""
import logging

from abom import log as logmod


def test_levels():
    logmod.setup(verbose=0)
    assert logging.getLogger("abom").level == logging.WARNING
    logmod.setup(verbose=1)
    assert logging.getLogger("abom").level == logging.INFO
    logmod.setup(verbose=2)
    assert logging.getLogger("abom").level == logging.DEBUG
    logmod.setup(quiet=True)
    assert logging.getLogger("abom").level == logging.ERROR


def test_handler_goes_to_stderr():
    logmod.setup(verbose=1)
    handlers = logging.getLogger("abom").handlers
    assert len(handlers) == 1
    import sys
    assert handlers[0].stream is sys.stderr
