"""Logging for the abom CLI.

Logs go to **stderr** so they never mix into the ABOM written to stdout.

  (default)    warnings + errors only
  -v           INFO  — high-level steps (what was scanned / verified)
  -vv          DEBUG — per-dependency / per-file / per-check detail
  -q / --quiet ERROR — errors only
"""
from __future__ import annotations

import logging
import sys

log = logging.getLogger("abom")


def setup(verbose: int = 0, quiet: bool = False) -> None:
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname).1s %(name)s | %(message)s"))
    root = logging.getLogger("abom")
    root.handlers[:] = [handler]
    root.setLevel(level)
    root.propagate = False
