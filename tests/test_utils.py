import pytest
from ecs_logging._utils import flatten_dict, de_dot, normalize_dict


def test_flatten_dict():
    assert flatten_dict(
        {"a": {"b": 1}, "a.c": {"d.e": {"f": 1}, "d.e.g": [{"f.c": 2}]}}
    ) == {"a.b": 1, "a.c.d.e.f": 1, "a.c.d.e.g": [{"f.c": 2}]}

    with pytest.raises(ValueError) as e:
        flatten_dict({"a": {"b": 1}, "a.b": 2})

    assert str(e.value) == "Duplicate entry for 'a.b' with different nesting"

    with pytest.raises(ValueError) as e:
        flatten_dict({"a": {"b": {"c": 1}}, "a.b": {"c": 2}, "a.b.c": 1})

    assert str(e.value) == "Duplicate entry for 'a.b.c' with different nesting"


def test_de_dot():
    assert de_dot("x.y.z", {"a": {"b": 1}}) == {"x": {"y": {"z": {"a": {"b": 1}}}}}


def test_normalize_dict():
    assert normalize_dict(
        {"a": {"b": 1}, "a.c": {"d.e": {"f": 1}, "d.e.g": [{"f.c": 2}]}}
    ) == {"a": {"b": 1, "c": {"d": {"e": {"f": 1, "g": [{"f": {"c": 2}}]}}}}}
