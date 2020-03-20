import json

try:
    import typing

    TYPE_CHECKING = typing.TYPE_CHECKING
except ImportError:
    typing = None  # type: ignore
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Any, Dict


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
