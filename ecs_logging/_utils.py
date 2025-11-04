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

import collections.abc
import json
import functools
import sys
from typing import Any, Dict, Mapping

if sys.version_info >= (3, 9):
    from collections.abc import MutableMapping
else:
    from typing import MutableMapping


__all__ = [
    "normalize_dict",
    "de_dot",
    "merge_dicts",
    "json_dumps",
]


def flatten_dict(value: Mapping[str, Any]) -> Dict[str, Any]:
    """Adds dots to all nested fields in dictionaries.
    Raises an error if there are entries which are represented
    with different forms of nesting. (ie {"a": {"b": 1}, "a.b": 2})
    """
    top_level = {}
    for key, val in value.items():
        if not isinstance(val, collections.abc.Mapping):
            if key in top_level:
                raise ValueError(f"Duplicate entry for '{key}' with different nesting")
            top_level[key] = val
        else:
            val = flatten_dict(val)
            for vkey, vval in val.items():
                vkey = f"{key}.{vkey}"
                if vkey in top_level:
                    raise ValueError(
                        f"Duplicate entry for '{vkey}' with different nesting"
                    )
                top_level[vkey] = vval

    return top_level


def normalize_dict(value: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Expands all dotted names to nested dictionaries"""
    if not isinstance(value, MutableMapping):
        return value
    keys = list(value.keys())
    for key in keys:
        if "." in key:
            merge_dicts(de_dot(key, value.pop(key)), value)
    for key, val in value.items():
        if isinstance(val, dict):
            normalize_dict(val)
        elif isinstance(val, list):
            val[:] = [normalize_dict(x) for x in val]
    return value


def de_dot(dot_string: str, msg: Any) -> Dict[str, Any]:
    """Turn value and dotted string key into a nested dictionary"""
    arr = dot_string.split(".")
    ret = {arr[-1]: msg}
    for i in range(len(arr) - 2, -1, -1):
        ret = {arr[i]: ret}
    return ret


def merge_dicts(
    from_: Mapping[Any, Any], into: MutableMapping[Any, Any]
) -> MutableMapping[Any, Any]:
    """Merge deeply nested dictionary structures.
    When called has side-effects within 'destination'.
    """
    for key, value in from_.items():
        into.setdefault(key, {})
        if isinstance(value, dict) and isinstance(into[key], dict):
            merge_dicts(value, into[key])
        elif into[key] != {}:
            raise TypeError(
                "Type mismatch at key `{}`: merging dicts would replace value `{}` with `{}`. This is likely due to "
                "dotted keys in the event dict being turned into nested dictionaries, causing a conflict.".format(
                    key, into[key], value
                )
            )
        else:
            into[key] = value
    return into


def json_dumps(value: MutableMapping[str, Any]) -> str:

    # Ensure that the first three fields are '@timestamp',
    # 'log.level', and 'message' per ECS spec
    ordered_fields = []
    try:
        ordered_fields.append(("@timestamp", value.pop("@timestamp")))
    except KeyError:
        pass

    # log.level can either be nested or not nested so we have to try both
    try:
        ordered_fields.append(("log.level", value["log"].pop("level")))
        if not value["log"]:  # Remove the 'log' dictionary if it's now empty
            value.pop("log", None)
    except KeyError:
        try:
            ordered_fields.append(("log.level", value.pop("log.level")))
        except KeyError:
            pass
    try:
        ordered_fields.append(("message", value.pop("message")))
    except KeyError:
        pass

    json_dumps = functools.partial(
        json.dumps, sort_keys=True, separators=(",", ":"), default=_json_dumps_fallback
    )

    # Because we want to use 'sorted_keys=True' we manually build
    # the first three keys and then build the rest with json.dumps()
    if ordered_fields:
        # Need to call json.dumps() on values just in
        # case the given values aren't strings (even though
        # they should be according to the spec)
        ordered_json = ",".join(f'"{k}":{json_dumps(v)}' for k, v in ordered_fields)
        if value:
            return "{{{},{}".format(
                ordered_json,
                json_dumps(value)[1:],
            )
        else:
            return "{%s}" % ordered_json
    # If there are no fields with ordering requirements we
    # pass everything into json.dumps()
    else:
        return json_dumps(value)


def _json_dumps_fallback(value: Any) -> Any:
    """
    Fallback handler for json.dumps to handle objects json doesn't know how to
    serialize.
    """
    try:
        # This is what structlog's json fallback does
        return value.__structlog__()
    except AttributeError:
        return repr(value)
