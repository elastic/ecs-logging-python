import pytest
from ecs_logging._utils import flatten_dict, de_dot, normalize_dict, json_dumps


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


def test_normalize_dict_with_array():
    assert normalize_dict({"a": ["1", "2"]}) == {"a": ["1", "2"]}


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        ({}, "{}"),
        ({"log": {"level": "info"}}, '{"log.level":"info"}'),
        ({"log.level": "info"}, '{"log.level":"info"}'),
        (
            {"log": {"level": "info", "message": "hello"}},
            '{"log.level":"info","log":{"message":"hello"}}',
        ),
        ({"@timestamp": "2021-01-01..."}, '{"@timestamp":"2021-01-01..."}'),
        ({"message": "hello"}, '{"message":"hello"}'),
        ({"message": 1}, '{"message":1}'),
        ({"message": ["hello"]}, '{"message":["hello"]}'),
        ({"message": {"key": "val"}}, '{"message":{"key":"val"}}'),
        ({"custom": "value"}, '{"custom":"value"}'),
        ({"log.level": "info"}, '{"log.level":"info"}'),
        (
            {"log": {"message": "hello"}, "message": "hello"},
            '{"message":"hello","log":{"message":"hello"}}',
        ),
        (
            {
                "log": {"message": "hello", "level": "info"},
                "message": "hello",
                "@timestamp": "2021-01-01...",
            },
            '{"@timestamp":"2021-01-01...","log.level":"info","message":"hello","log":{"message":"hello"}}',
        ),
        (
            {
                "log": {"level": "info"},
                "message": "hello",
                "@timestamp": "2021-01-01...",
            },
            '{"@timestamp":"2021-01-01...","log.level":"info","message":"hello"}',
        ),
    ],
)
def test_json_dumps(value, expected):
    assert json_dumps(value) == expected
