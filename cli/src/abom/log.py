"""Logging for the abom CLI.

Logs go to **stderr** so they never mix into the ABOM written to stdout.

  (default)      warnings + errors only
  -v             INFO  — high-level steps (what was scanned / verified)
  -vv            DEBUG — per-dependency / per-file / per-check detail
  -q / --quiet   ERROR — errors only
  --json-logs    one NDJSON object per line on stderr (for CI pipelines)
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import sys

log = logging.getLogger("abom")

# Standard LogRecord attributes — everything else is treated as structured extra.
_STD = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message", "asctime",
}


class JsonFormatter(logging.Formatter):
    """Render each record as a single JSON line, including any ``extra=`` fields."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": _dt.datetime.fromtimestamp(record.created, _dt.timezone.utc)
                     .isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _STD and not key.startswith("_"):
                data[key] = value
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def setup(verbose: int = 0, quiet: bool = False, json_logs: bool = False) -> None:
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        JsonFormatter() if json_logs
        else logging.Formatter("%(levelname).1s %(name)s | %(message)s")
    )
    root = logging.getLogger("abom")
    root.handlers[:] = [handler]
    root.setLevel(level)
    root.propagate = False
