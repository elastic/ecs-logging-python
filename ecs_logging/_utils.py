def de_dot(dot_string, msg):
    # type: (str, str) -> dict
    """Turn message and dotted string into a nested dictionary"""
    arr = dot_string.split(".")
    ret = {arr[-1]: msg}
    for i in range(len(arr) - 2, -1, -1):
        ret = {arr[i]: ret}
    return ret


def deepmerge(source, destination):
    # type: (dict, dict) -> None
    """Merge deeply nested dictionary structures.
    When called has side-effects within 'destination'.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            deepmerge(value, destination.setdefault(key, {}))
        else:
            destination[key] = value
