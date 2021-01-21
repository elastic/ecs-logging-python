import logging
import time
from traceback import format_tb
from ._meta import ECS_VERSION
from ._utils import (
    merge_dicts,
    de_dot,
    json_dumps,
    TYPE_CHECKING,
    collections_abc,
    lru_cache,
    flatten_dict,
)

if TYPE_CHECKING:
    from typing import Optional, Any, Callable, Dict, Sequence


# Load the attributes of a LogRecord so if some are
# added in the future we won't mistake them for 'extra=...'
try:
    _LOGRECORD_DIR = set(dir(logging.LogRecord("", 0, "", 0, "", (), None)))
except Exception:  # LogRecord signature changed?
    _LOGRECORD_DIR = set()


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
    } | _LOGRECORD_DIR
    converter = time.gmtime

    def __init__(self, stack_trace_limit=None, exclude_fields=()):
        # type: (Any, Optional[int], Sequence[str]) -> None
        """Initialize the ECS formatter.

        :param int stack_trace_limit:
            Specifies the maximum number of frames to include for stack
            traces. Defaults to ``None`` which includes all available frames.
            Setting this to zero will suppress stack traces.
            This setting doesn't affect ``LogRecord.stack_info`` because
            this attribute is typically already pre-formatted.
        :param Sequence[str] exclude_fields:
            Specifies any fields that should be suppressed from the resulting
            fields, expressed with dot notation::

                exclude_keys=["error.stack_trace"]

            You can also use field prefixes to exclude whole groups of fields::

                exclude_keys=["error"]
        """
        super(StdlibFormatter, self).__init__()

        if stack_trace_limit is not None:
            if not isinstance(stack_trace_limit, int):
                raise TypeError(
                    "'stack_trace_limit' must be None, or a non-negative integer"
                )
            elif stack_trace_limit < 0:
                raise ValueError(
                    "'stack_trace_limit' must be None, or a non-negative integer"
                )

        if (
            not isinstance(exclude_fields, collections_abc.Sequence)
            or isinstance(exclude_fields, str)
            or any(not isinstance(item, str) for item in exclude_fields)
        ):
            raise TypeError("'exclude_fields' must be a sequence of strings")

        self._exclude_fields = frozenset(exclude_fields)
        self._stack_trace_limit = stack_trace_limit

    def format(self, record):
        # type: (logging.LogRecord) -> str
        result = self.format_to_ecs(record)
        return json_dumps(result)

    def format_to_ecs(self, record):
        # type: (logging.LogRecord) -> Dict[str, Any]
        """Function that can be overridden to add additional fields to
        (or remove fields from) the JSON before being dumped into a string.

         .. code-block: python

            class MyFormatter(StdlibFormatter):
                def format_to_ecs(self, record):
                  result = super().format_to_ecs(record)
                  del result["log"]["original"]   # remove unwanted field(s)
                  result["my_field"] = "my_value" # add custom field
                  return result
        """

        extractors = {
            "@timestamp": self._record_timestamp,
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
            "error.stack_trace": self._record_error_stack_trace,
        }  # type: Dict[str, Callable[[logging.LogRecord],Any]]

        result = {}  # type: Dict[str, Any]
        for field in set(extractors.keys()).difference(self._exclude_fields):
            if self._is_field_excluded(field):
                continue
            value = extractors[field](record)
            if value is not None:
                merge_dicts(de_dot(field, value), result)

        available = record.__dict__

        # This is cleverness because 'message' is NOT a member
        # key of ``record.__dict__`` the ``getMessage()`` method
        # is effectively ``msg % args`` (actual keys) By manually
        # adding 'message' to ``available``, it simplifies the code
        available["message"] = record.getMessage()

        # Pull all extras and flatten them to be sent into '_is_field_excluded'
        # since they can be defined as 'extras={"http": {"method": "GET"}}'
        extra_keys = set(available).difference(self._LOGRECORD_DICT)
        extras = flatten_dict({key: available[key] for key in extra_keys})

        # Pop all Elastic APM extras and add them
        # to standard tracing ECS fields.
        extras["span.id"] = extras.pop("elasticapm_span_id", None)
        extras["transaction.id"] = extras.pop("elasticapm_transaction_id", None)
        extras["trace.id"] = extras.pop("elasticapm_trace_id", None)
        extras["service.name"] = extras.pop("elasticapm_service_name", None)

        # Merge in any keys that were set within 'extra={...}'
        for field, value in extras.items():
            if field.startswith("elasticapm_labels."):
                continue  # Unconditionally remove, we don't need this info.
            if value is None or self._is_field_excluded(field):
                continue
            merge_dicts(de_dot(field, value), result)

        # The following is mostly for the ecs format. You can't have 2x
        # 'message' keys in _WANTED_ATTRS, so we set the value to
        # 'log.original' in ecs, and this code block guarantees it
        # still appears as 'message' too.
        if not self._is_field_excluded("message"):
            result.setdefault("message", available["message"])
        return result

    @lru_cache()
    def _is_field_excluded(self, field):
        # type: (str) -> bool
        field_path = []
        for path in field.split("."):
            field_path.append(path)
            if ".".join(field_path) in self._exclude_fields:
                return True
        return False

    def _record_timestamp(self, record):
        # type: (logging.LogRecord) -> str
        return "%s.%03dZ" % (
            self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            record.msecs,
        )

    def _record_attribute(self, attribute):
        # type: (str) -> Callable[[logging.LogRecord], Optional[Any]]
        return lambda r: getattr(r, attribute, None)

    def _record_error_stack_trace(self, record):
        # type: (logging.LogRecord) -> Optional[str]
        # Using stack_info=True will add 'error.stack_trace' even
        # if the type is not 'error', exc_info=True only gathers
        # when there's an active exception.
        if (
            record.exc_info
            and record.exc_info[2] is not None
            and (self._stack_trace_limit is None or self._stack_trace_limit > 0)
        ):
            return (
                "".join(format_tb(record.exc_info[2], limit=self._stack_trace_limit))
                or None
            )
        # LogRecord only has 'stack_info' if it's passed via .log(..., stack_info=True)
        stack_info = getattr(record, "stack_info", None)
        if stack_info:
            return str(stack_info)
        return None
