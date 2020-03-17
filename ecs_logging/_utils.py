def de_dot(dot_string, msg):
    """Turn message and dotted string into a nested dictionary"""
    arr = dot_string.split(".")
    ret = {arr[-1]: msg}
    for idx in range(len(arr), 1, -1):
        ret = {arr[idx - 2]: ret}
    return ret


def deepmerge(source, destination):
    """Merge deeply nested dictionary structures"""
    for key, value in source.items():
        if isinstance(value, dict):
            deepmerge(value, destination.setdefault(key, {}))
        else:
            destination[key] = value
