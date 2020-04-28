import time
import datetime
from ._meta import ECS_VERSION
from ._utils import json_dumps, normalize_dict, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict


class StructlogFormatter:
    """ECS formatter for the ``structlog`` module"""

    def __call__(self, _, name, event_dict):
        # type: (Any, str, Dict[str, Any]) -> str
        event_dict = normalize_dict(event_dict)
        event_dict.setdefault("log", {}).setdefault("level", name.lower())
        event_dict = self.format_to_ecs(event_dict)
        return json_dumps(event_dict)

    def format_to_ecs(self, event_dict):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        event_dict["message"] = event_dict.pop("event")
        if "@timestamp" not in event_dict:
            event_dict["@timestamp"] = (
                datetime.datetime.utcfromtimestamp(time.time()).strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"
                )[:-3]
                + "Z"
            )
        event_dict.setdefault("ecs", {}).setdefault("version", ECS_VERSION)
        return event_dict
