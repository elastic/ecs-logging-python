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
from ._meta import ECS_VERSION
from ._utils import json_dumps, normalize_dict, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict


class StructlogFormatter:
    """ECS formatter for the ``structlog`` module"""

    def __call__(self, _, name, event_dict):
        # type: (Any, str, Dict[str, Any]) -> str

        # Handle event -> message now so that stuff like `event.dataset` doesn't
        # cause problems down the line
        event_dict["message"] = str(event_dict.pop("event"))
        event_dict = normalize_dict(event_dict)
        event_dict.setdefault("log", {}).setdefault("level", name.lower())
        event_dict = self.format_to_ecs(event_dict)
        return json_dumps(event_dict)

    def format_to_ecs(self, event_dict):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        if "@timestamp" not in event_dict:
            event_dict["@timestamp"] = (
                datetime.datetime.utcfromtimestamp(time.time()).strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"
                )[:-3]
                + "Z"
            )
        event_dict.setdefault("ecs", {}).setdefault("version", ECS_VERSION)
        return event_dict
