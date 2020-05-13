try:
    from collections.abc import Sequence as Seq
except AttributeError:
    from collections import Sequence as Seq

import logging
import time
from traceback import format_tb
from ._meta import ECS_VERSION
from ._utils import merge_dicts, de_dot, json_dumps, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Sequence


class StdlibFormatter(logging.Formatter):
    """ECS Formatter for the standard library ``logging`` module"""

    _LOGRECORD_DICT = {
        "name",
        "msg",
        "args",
        "asctime",
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
        "message",
    }
    converter = time.gmtime

    def __init__(self, stack_trace_limit=None, exclude_keys=[]):
        # type: (Any, Sequence[str]) -> None
        """Initialize the ECS formatter.

        Parameters
        ----------
        stack_trace_limit : int
          Specifies the maximum number of frames to include for stack
          traces. Defaults to `None`, which includes all available frames.
          Setting this to zero will suppress stack traces.
        exclude_keys : Sequence[str]
          Specifies any fields that should be suppressed from the resulting
          fields, expressed with dot notation. For example:
          `exclude_keys=["error.stack_trace"]`
        """
        super(StdlibFormatter, self).__init__()
        if stack_trace_limit is not None and (
            type(stack_trace_limit) != int or stack_trace_limit < 0
        ):
            raise ValueError(
                "stack_trace_limit must be None, or a non-negative integer"
            )
        if not isinstance(exclude_keys, Seq) or list(
            filter(lambda x: type(x) != str, exclude_keys)
        ):
            raise ValueError("exclude_keys must be a sequence of strings")
        self._exclude_keys = exclude_keys
        self._stack_trace_limit = stack_trace_limit

    def format(self, record):
        # type: (logging.LogRecord) -> str
        result = self.format_to_ecs(record)
        return json_dumps(result)

    def format_to_ecs(self, record):
        # type: (logging.LogRecord) -> Dict[str, Any]
        """Function that can be overridden to add additional fields to
        (or remove fields from) the JSON before being dumped into a string.
        Example:
          class MyFormatter(StdlibFormatter):
            def format_to_ecs(self, record):
              result = super().format_to_ecs(record)
              del result["log"]["original"]   # remove unwanted field(s)
              result["my_field"] = "my_value" # add custom field
              return result
        """

        extractors = {
            "@timestamp": lambda r: self._format_timestamp(r),
            "ecs.version": lambda _: ECS_VERSION,
            "log.level": lambda r: (r.levelname.lower() if r.levelname else None),
            "log.origin.function": self._record_attribute("funcName"),
            "log.origin.file.line": self._record_attribute("lineno"),
            "log.origin.file.name": self._record_attribute("filename"),
            "log.original": lambda r: r.getMessage(),
            "log.logger": self._record_attribute("name"),
            "process.pid": self._record_attribute("process"),
            "process.name": self._record_attribute("processName"),
            "process.thread.id": self._record_attribute("thread"),
            "process.thread.name": self._record_attribute("threadName"),
            "error.type": lambda r: (
                r.exc_info[0].__name__
                if (r.exc_info is not None and r.exc_info[0] is not None)
                else None
            ),
            "error.message": lambda r: (
                str(r.exc_info[1]) if r.exc_info and r.exc_info[1] else None
            ),
            "error.stack_trace": lambda r: (
                "".join(format_tb(r.exc_info[2], limit=self._stack_trace_limit))
                if r.exc_info and r.exc_info[2]
                else None
            ),
        }  # type: Dict[str, Callable[[logging.LogRecord],Any]]

        result = {}  # type: Dict[str,Any]
        for key in set(extractors.keys()).difference(self._exclude_keys):
            value = extractors[key](record)
            if value is not None:
                merge_dicts(de_dot(key, value), result)

        available = record.__dict__

        # This is cleverness because 'message' is NOT a member
        # key of ``record.__dict__`` the ``getMessage()`` method
        # is effectively ``msg % args`` (actual keys) By manually
        # adding 'message' to ``available``, it simplifies the code
        available["message"] = record.getMessage()

        extras = set(available).difference(self._LOGRECORD_DICT)
        # Merge in any keys that were set within 'extra={...}'
        for key in extras:
            merge_dicts(de_dot(key, available[key]), result)

        # The following is mostly for the ecs format. You can't have 2x
        # 'message' keys in _WANTED_ATTRS, so we set the value to
        # 'log.original' in ecs, and this code block guarantees it
        # still appears as 'message' too.
        result.setdefault("message", available["message"])
        return result

    def _format_timestamp(self, record):
        # type: (logging.LogRecord) -> str
        return "%s.%03dZ" % (
            self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            record.msecs,
        )

    def _record_attribute(self, attribute):
        # type: (str) -> Callable[[logging.LogRecord],Any]
        return lambda r: getattr(r, attribute, None)
