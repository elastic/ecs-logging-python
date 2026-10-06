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

from collections.abc import MutableMapping
import json
from io import StringIO
from unittest import mock

import pytest
import structlog

import ecs_logging


class NotADict(MutableMapping):
    def __init__(self, data):
        self._data = dict(data)

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __setitem__(self, key, value):
        self._data.__setitem__(key, value)

    def __delitem__(self, key):
        return self._data.__delitem__(key)

    def __iter__(self):
        return self._data.__iter__()

    def __len__(self):
        return self._data.__len__()


class NotSerializable:
    def __repr__(self):
        return "<NotSerializable>"


@pytest.fixture(params=[False, True], ids=["dict", "mapping"])
def event(request):
    data = {
        "event": "test message",
        "log.logger": "logger-name",
        "foo": "bar",
        "baz": NotSerializable(),
    }
    if request.param:
        return NotADict(data)
    return data


@pytest.fixture(params=[False, True], ids=["dict", "mapping"])
def event_with_exception(request):
    data = {
        "event": "test message",
        "log.logger": "logger-name",
        "foo": "bar",
        "exception": "<stack trace here>",
    }
    if request.param:
        return NotADict(data)
    return data


def test_conflicting_event_dict(event):
    formatter = ecs_logging.StructlogFormatter()
    event["foo.bar"] = "baz"
    with pytest.raises(TypeError):
        formatter(None, "debug", event)


@mock.patch("time.time")
def test_event_dict_formatted(time, spec_validator, event):
    time.return_value = 1584720997.187709

    formatter = ecs_logging.StructlogFormatter()
    assert spec_validator(formatter(None, "debug", event)) == (
        '{"@timestamp":"2020-03-20T16:16:37.187Z","log.level":"debug",'
        '"message":"test message",'
        '"baz":"<NotSerializable>",'
        '"ecs.version":"1.6.0",'
        '"foo":"bar",'
        '"log":{"logger":"logger-name"}}'
    )


@mock.patch("time.time")
def test_can_be_set_as_processor(time, spec_validator):
    time.return_value = 1584720997.187709

    stream = StringIO()
    structlog.configure(
        processors=[ecs_logging.StructlogFormatter()],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(stream),
    )

    logger = structlog.get_logger("logger-name")
    logger.debug("test message", custom="key", **{"dot.ted": 1})

    assert spec_validator(stream.getvalue()) == (
        '{"@timestamp":"2020-03-20T16:16:37.187Z","log.level":"debug",'
        '"message":"test message","custom":"key","dot":{"ted":1},'
        '"ecs.version":"1.6.0"}\n'
    )


def test_exception_log_is_ecs_compliant_when_used_with_format_exc_info(
    event_with_exception,
):
    formatter = ecs_logging.StructlogFormatter()
    formatted_event_dict = json.loads(formatter(None, "debug", event_with_exception))

    assert (
        "exception" not in formatted_event_dict
    ), "The key 'exception' at the root of a log is not ECS-compliant"
    assert "error" in formatted_event_dict
    assert "stack_trace" in formatted_event_dict["error"]
    assert "<stack trace here>" in formatted_event_dict["error"]["stack_trace"]


@mock.patch("time.time")
def test_ensure_ascii_default(time):
    """Test that ensure_ascii defaults to True (escaping non-ASCII characters)"""
    time.return_value = 1584720997.187709

    formatter = ecs_logging.StructlogFormatter()
    result = formatter(None, "debug", {"event": "Hello 世界", "log.logger": "test"})

    # With ensure_ascii=True (default), non-ASCII characters should be escaped
    assert "\\u4e16\\u754c" in result
    assert "世界" not in result

    # Verify the JSON is valid
    parsed = json.loads(result)
    assert parsed["message"] == "Hello 世界"


@mock.patch("time.time")
def test_ensure_ascii_true(time):
    """Test that ensure_ascii=True escapes non-ASCII characters"""
    time.return_value = 1584720997.187709

    formatter = ecs_logging.StructlogFormatter(ensure_ascii=True)
    result = formatter(None, "info", {"event": "Café ☕", "log.logger": "test"})

    # With ensure_ascii=True, non-ASCII characters should be escaped
    assert "\\u00e9" in result  # é is escaped
    assert "\\u2615" in result  # ☕ is escaped
    assert "Café" not in result
    assert "☕" not in result

    # Verify the JSON is valid and correctly decoded
    parsed = json.loads(result)
    assert parsed["message"] == "Café ☕"


@mock.patch("time.time")
def test_ensure_ascii_false(time):
    """Test that ensure_ascii=False preserves non-ASCII characters"""
    time.return_value = 1584720997.187709

    formatter = ecs_logging.StructlogFormatter(ensure_ascii=False)
    result = formatter(None, "debug", {"event": "Hello 世界", "log.logger": "test"})

    # With ensure_ascii=False, non-ASCII characters should be preserved
    assert "世界" in result
    assert "\\u4e16" not in result

    # Verify the JSON is valid
    parsed = json.loads(result)
    assert parsed["message"] == "Hello 世界"


@mock.patch("time.time")
def test_ensure_ascii_false_with_emoji(time):
    """Test that ensure_ascii=False preserves emoji and special characters"""
    time.return_value = 1584720997.187709

    formatter = ecs_logging.StructlogFormatter(ensure_ascii=False)
    result = formatter(None, "info", {"event": "Café ☕ 你好", "log.logger": "test"})

    # With ensure_ascii=False, all non-ASCII characters should be preserved
    assert "Café" in result
    assert "☕" in result
    assert "你好" in result

    # Verify the JSON is valid and correctly decoded
    parsed = json.loads(result)
    assert parsed["message"] == "Café ☕ 你好"


@mock.patch("time.time")
def test_ensure_ascii_with_custom_fields(time):
    """Test that ensure_ascii works with custom fields containing non-ASCII"""
    time.return_value = 1584720997.187709

    formatter = ecs_logging.StructlogFormatter(ensure_ascii=False)
    result = formatter(
        None,
        "info",
        {
            "event": "Test",
            "log.logger": "test",
            "user": "用户",
            "city": "北京",
        },
    )

    # With ensure_ascii=False, non-ASCII in custom fields should be preserved
    assert "用户" in result
    assert "北京" in result

    # Verify the JSON is valid
    parsed = json.loads(result)
    assert parsed["user"] == "用户"
    assert parsed["city"] == "北京"


@pytest.mark.parametrize(
    ["method_name", "level"],
    [
        ("exception", "error"),
        ("warn", "warning"),
        ("warning", "warning"),
        ("critical", "critical"),
    ],
)
def test_method_name_mapped_to_log_level(event, method_name, level):
    formatter = ecs_logging.StructlogFormatter()
    ecs = json.loads(formatter(None, method_name, event))
    assert ecs["log.level"] == level


def test_exception_method_logs_error_level():
    stream = StringIO()
    structlog.configure(
        processors=[ecs_logging.StructlogFormatter()],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(stream),
    )
    logger = structlog.get_logger("logger-name")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oops")

    ecs = json.loads(stream.getvalue().rstrip())
    assert ecs["log.level"] == "error"
