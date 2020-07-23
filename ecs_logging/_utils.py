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
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
