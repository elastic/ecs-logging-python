import logging
import time
from ._meta import ECS_VERSION
from ._utils import merge_dicts, de_dot, json_dumps, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict


class StdlibFormatter(logging.Formatter):
    """ECS Formatter for the standard library ``logging`` module"""

    WANTED_ATTRS = {
        "levelname": "log.level",
        "funcName": "log.origin.function",
        "lineno": "log.origin.file.line",
        "filename": "log.origin.file.name",
        "message": "log.original",
        "name": "log.logger",
    }
    LOGRECORD_DICT = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
    }
    converter = time.gmtime

    def __init__(self):
        # type: () -> None
        super(StdlibFormatter, self).__init__()

    def format(self, record):
        # type: (logging.LogRecord) -> str
        result = self.format_to_ecs(record)
        return json_dumps(result)

    def format_to_ecs(self, record):
        # type: (logging.LogRecord) -> Dict[str, Any]
        """Function that can be overridden to add additional fields
        to the JSON before being dumped into a string.
        """
        timestamp = "%s.%03dZ" % (
            self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            record.msecs,
        )
        result = {"@timestamp": timestamp, "ecs": {"version": ECS_VERSION}}
        available = record.__dict__

        # This is cleverness because 'message' is NOT a member
        # key of ``record.__dict__`` the ``getMessage()`` method
        # is effectively ``msg % args`` (actual keys) By manually
        # adding 'message' to ``available``, it simplifies the code
        available["message"] = record.getMessage()

        for attribute in set(self.WANTED_ATTRS).intersection(available):
            ecs_attr = self.WANTED_ATTRS[attribute]
            value = getattr(record, attribute)
            if ecs_attr == "log.level" and isinstance(value, str):
                value = value.lower()
            merge_dicts(de_dot(ecs_attr, value), result)

        # Merge in any keys that were set within 'extra={...}'
        for key in set(available.keys()).difference(self.LOGRECORD_DICT):
            merge_dicts(de_dot(key, available[key]), result)

        # The following is mostly for the ecs format. You can't have 2x
        # 'message' keys in WANTED_ATTRS, so we set the value to
        # 'log.original' in ecs, and this code block guarantees it
        # still appears as 'message' too.
        result.setdefault("message", available["message"])
        return result
