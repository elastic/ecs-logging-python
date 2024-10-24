# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import time
import datetime
import sys
from typing import Any

if sys.version_info >= (3, 9):
    from collections.abc import MutableMapping
else:
    from typing import MutableMapping

from ._meta import ECS_VERSION
from ._utils import json_dumps, normalize_dict


class StructlogFormatter:
    """ECS formatter for the ``structlog`` module"""

    def __call__(self, _: Any, name: str, event_dict: MutableMapping[str, Any]) -> str:

        # Handle event -> message now so that stuff like `event.dataset` doesn't
        # cause problems down the line
        event_dict["message"] = str(event_dict.pop("event"))
        event_dict = normalize_dict(event_dict)
        event_dict.setdefault("log", {}).setdefault("level", name.lower())
        event_dict = self.format_to_ecs(event_dict)
        return self._json_dumps(event_dict)

    def format_to_ecs(
        self, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        if "@timestamp" not in event_dict:
            event_dict["@timestamp"] = (
                datetime.datetime.fromtimestamp(
                    time.time(), tz=datetime.timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                + "Z"
            )

        if "exception" in event_dict:
            stack_trace = event_dict.pop("exception")
            if "error" in event_dict:
                event_dict["error"]["stack_trace"] = stack_trace
            else:
                event_dict["error"] = {"stack_trace": stack_trace}

        event_dict.setdefault("ecs.version", ECS_VERSION)
        return event_dict

    def _json_dumps(self, value: MutableMapping[str, Any]) -> str:
        return json_dumps(value=value)
