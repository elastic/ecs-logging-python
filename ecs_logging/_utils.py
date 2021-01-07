import json

try:
    import typing

    TYPE_CHECKING = typing.TYPE_CHECKING
except ImportError:
    typing = None  # type: ignore
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Any, Dict

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache  # type: ignore


__all__ = [
    "collections_abc",
    "normalize_dict",
    "de_dot",
    "merge_dicts",
    "json_dumps",
    "TYPE_CHECKING",
    "typing",
    "lru_cache",
]


def flatten_dict(value):
    # type: (typing.Mapping[str, Any]) -> Dict[str, Any]
    """Adds dots to all nested fields in dictionaries.
    Raises an error if there are entries which are represented
    with different forms of nesting. (ie {"a": {"b": 1}, "a.b": 2})
    """
    top_level = {}
    for key, val in value.items():
        if not isinstance(val, collections_abc.Mapping):
            if key in top_level:
                raise ValueError(
                    "Duplicate entry for '%s' with different nesting" % key
                )
            top_level[key] = val
        else:
            val = flatten_dict(val)
            for vkey, vval in val.items():
                vkey = "%s.%s" % (key, vkey)
                if vkey in top_level:
                    raise ValueError(
                        "Duplicate entry for '%s' with different nesting" % vkey
                    )
                top_level[vkey] = vval

    return top_level


def normalize_dict(value):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """Expands all dotted names to nested dictionaries"""
    if not isinstance(value, dict):
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


def de_dot(dot_string, msg):
    # type: (str, Any) -> Dict[str, Any]
    """Turn value and dotted string key into a nested dictionary"""
    arr = dot_string.split(".")
    ret = {arr[-1]: msg}
    for i in range(len(arr) - 2, -1, -1):
        ret = {arr[i]: ret}
    return ret


def merge_dicts(from_, into):
    # type: (Dict[Any, Any], Dict[Any, Any]) -> Dict[Any, Any]
    """Merge deeply nested dictionary structures.
    When called has side-effects within 'destination'.
    """
    for key, value in from_.items():
        if isinstance(value, dict):
            merge_dicts(value, into.setdefault(key, {}))
        else:
            into[key] = value
    return into


def json_dumps(value):
    # type: (Dict[str, Any]) -> str

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

    # Because we want to use 'sorted_keys=True' we manually build
    # the first three keys and then build the rest with json.dumps()
    if ordered_fields:
        # Need to call json.dumps() on values just in
        # case the given values aren't strings (even though
        # they should be according to the spec)
        ordered_json = ",".join(
            '"%s":%s' % (k, json.dumps(v, sort_keys=True, separators=(",", ":")))
            for k, v in ordered_fields
        )
        if value:
            return "{%s,%s" % (
                ordered_json,
                json.dumps(value, sort_keys=True, separators=(",", ":"))[1:],
            )
        else:
            return "{%s}" % ordered_json
    # If there are no fields with ordering requirements we
    # pass everything into json.dumps()
    else:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
