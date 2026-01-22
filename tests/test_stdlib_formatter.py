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

import logging
import logging.config
from unittest import mock
import pytest
import json
import time
import random
import ecs_logging
from io import StringIO


@pytest.fixture(scope="function")
def logger():
    return logging.getLogger(f"test-logger-{time.time():f}-{random.random():f}")


def make_record():
    record = logging.LogRecord(
        name="logger-name",
        level=logging.DEBUG,
        pathname="/path/file.py",
        lineno=10,
        msg="%d: %s",
        args=(1, "hello"),
        func="test_function",
        exc_info=None,
    )
    record.created = 1584713566
    record.msecs = 123
    return record


def test_record_formatted(spec_validator):
    formatter = ecs_logging.StdlibFormatter(exclude_fields=["process"])

    assert spec_validator(formatter.format(make_record())) == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","log.level":"debug","message":"1: hello","ecs.version":"1.6.0",'
        '"log":{"logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},"function":"test_function"},'
        '"original":"1: hello"}}'
    )


def test_extra_global_is_merged(spec_validator):
    formatter = ecs_logging.StdlibFormatter(
        exclude_fields=["process"], extra={"environment": "dev"}
    )

    assert spec_validator(formatter.format(make_record())) == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","log.level":"debug","message":"1: hello","ecs.version":"1.6.0",'
        '"environment":"dev",'
        '"log":{"logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},"function":"test_function"},'
        '"original":"1: hello"}}'
    )


def test_can_be_overridden(spec_validator):
    class CustomFormatter(ecs_logging.StdlibFormatter):
        def format_to_ecs(self, record):
            ecs_dict = super().format_to_ecs(record)
            ecs_dict["custom"] = "field"
            return ecs_dict

    formatter = CustomFormatter(exclude_fields=["process"])
    assert spec_validator(formatter.format(make_record())) == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","log.level":"debug","message":"1: hello",'
        '"custom":"field","ecs.version":"1.6.0","log":{"logger":"logger-name","origin":'
        '{"file":{"line":10,"name":"file.py"},"function":"test_function"},"original":"1: hello"}}'
    )


def test_can_be_set_on_handler():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter(exclude_fields=["process"]))

    handler.handle(make_record())

    assert stream.getvalue() == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","log.level":"debug","message":"1: hello",'
        '"ecs.version":"1.6.0","log":{"logger":"logger-name","origin":{"file":{"line":10,'
        '"name":"file.py"},"function":"test_function"},"original":"1: hello"}}\n'
    )


@mock.patch("time.time_ns")
@mock.patch("time.time")
def test_extra_is_merged(time, time_ns, logger):
    time.return_value = 1584720997.187709
    time_ns.return_value = time.return_value * 1_000_000_000

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        ecs_logging.StdlibFormatter(exclude_fields=["process", "tls.client"])
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info(
        "hey world",
        extra={
            "tls": {
                "cipher": "AES",
                "client": {"hash": {"md5": "0F76C7F2C55BFD7D8E8B8F4BFBF0C9EC"}},
            },
            "tls.established": True,
            "tls.client.certificate": "cert",
        },
    )

    ecs = json.loads(stream.getvalue().rstrip())
    assert isinstance(ecs["log"]["origin"]["file"].pop("line"), int)
    assert ecs == {
        "@timestamp": "2020-03-20T16:16:37.187Z",
        "ecs.version": "1.6.0",
        "log.level": "info",
        "log": {
            "logger": logger.name,
            "origin": {
                "file": {"name": "test_stdlib_formatter.py"},
                "function": "test_extra_is_merged",
            },
            "original": "hey world",
        },
        "message": "hey world",
        "tls": {"cipher": "AES", "established": True},
    }


@pytest.mark.parametrize("kwargs", [{}, {"stack_trace_limit": None}])
def test_stack_trace_limit_default(kwargs, logger):
    def f():
        g()

    def g():
        h()

    def h():
        raise ValueError("error!")

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter(**kwargs))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        f()
    except ValueError:
        logger.info("there was an error", exc_info=True)

    ecs = json.loads(stream.getvalue().rstrip())
    error_stack_trace = ecs["error"].pop("stack_trace")
    assert all(x in error_stack_trace for x in ("f()", "g()", "h()"))


@pytest.mark.parametrize("stack_trace_limit", [0, False])
def test_stack_trace_limit_disabled(stack_trace_limit, logger):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        ecs_logging.StdlibFormatter(stack_trace_limit=stack_trace_limit)
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        raise ValueError("error!")
    except ValueError:
        logger.info("there was an error", exc_info=True)

    ecs = json.loads(stream.getvalue().rstrip())
    assert ecs["error"] == {"message": "error!", "type": "ValueError"}
    assert ecs["log.level"] == "info"
    assert ecs["message"] == "there was an error"
    assert ecs["log"]["original"] == "there was an error"


def test_exc_info_false_does_not_raise(logger):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("there was %serror", "no ", exc_info=False)

    ecs = json.loads(stream.getvalue().rstrip())
    assert ecs["log.level"] == "info"
    assert ecs["message"] == "there was no error"
    assert "error" not in ecs


@pytest.mark.parametrize(
    ("stack_trace_limit", "expected_in", "expected_not_in"),
    [
        (2, ("f()", "g()"), ("h()",)),
        (-2, ("h()",), ("f()", "g()")),
    ],
)
def test_stack_trace_limit_traceback(
    stack_trace_limit, expected_in, expected_not_in, logger
):
    def f():
        g()

    def g():
        h()

    def h():
        raise ValueError("error!")

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter(stack_trace_limit=stack_trace_limit))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        f()
    except ValueError:
        logger.info("there was an error", exc_info=True)

    ecs = json.loads(stream.getvalue().rstrip())
    error_stack_trace = ecs["error"].pop("stack_trace")
    assert all(x in error_stack_trace for x in expected_in)
    assert all(x not in error_stack_trace for x in expected_not_in)
    assert ecs["error"] == {
        "message": "error!",
        "type": "ValueError",
    }
    assert ecs["log.level"] == "info"
    assert ecs["message"] == "there was an error"
    assert ecs["log"]["original"] == "there was an error"


def test_stack_trace_limit_types_and_values():
    with pytest.raises(TypeError) as e:
        ecs_logging.StdlibFormatter(stack_trace_limit="a")
    assert str(e.value) == "'stack_trace_limit' must be None or an integer"


@pytest.mark.parametrize(
    "exclude_fields",
    [
        "process",
        "log",
        "log.level",
        "message",
        ["log.origin", "log.origin.file", "log.origin.file.line"],
    ],
)
def test_exclude_fields(exclude_fields):
    if isinstance(exclude_fields, str):
        exclude_fields = [exclude_fields]
    formatter = ecs_logging.StdlibFormatter(exclude_fields=exclude_fields)
    ecs = formatter.format_to_ecs(make_record())

    for entry in exclude_fields:
        field_path = entry.split(".")
        try:
            obj = ecs
            for path in field_path[:-1]:
                obj = obj[path]
        except KeyError:
            continue
        assert field_path[-1] not in obj


@pytest.mark.parametrize(
    "exclude_fields",
    [
        "ecs.version",
    ],
)
def test_exclude_fields_not_dedotted(exclude_fields):
    formatter = ecs_logging.StdlibFormatter(exclude_fields=[exclude_fields])
    ecs = formatter.format_to_ecs(make_record())
    for entry in exclude_fields:
        assert entry not in ecs


def test_exclude_fields_empty_json_object():
    """Assert that if all JSON objects attributes are excluded then the object doesn't appear."""
    formatter = ecs_logging.StdlibFormatter(
        exclude_fields=["process.pid", "process.name", "process.thread"]
    )
    ecs = formatter.format_to_ecs(make_record())
    assert "process" not in ecs

    formatter = ecs_logging.StdlibFormatter(exclude_fields=["ecs.version"])
    ecs = formatter.format_to_ecs(make_record())
    assert "ecs" not in ecs


def test_exclude_fields_type_and_values():
    with pytest.raises(TypeError) as e:
        ecs_logging.StdlibFormatter(exclude_fields="a")
    assert str(e.value) == "'exclude_fields' must be a sequence of strings"

    with pytest.raises(TypeError) as e:
        ecs_logging.StdlibFormatter(exclude_fields={"a"})
    assert str(e.value) == "'exclude_fields' must be a sequence of strings"

    with pytest.raises(TypeError) as e:
        ecs_logging.StdlibFormatter(exclude_fields=[1])
    assert str(e.value) == "'exclude_fields' must be a sequence of strings"


def test_stack_info(logger):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("stack info!", stack_info=True)

    ecs = json.loads(stream.getvalue().rstrip())
    assert list(ecs["error"].keys()) == ["stack_trace"]
    error_stack_trace = ecs["error"].pop("stack_trace")
    assert "test_stack_info" in error_stack_trace and __file__ in error_stack_trace


@pytest.mark.parametrize("exclude_fields", [["error"], ["error.stack_trace"]])
def test_stack_info_excluded(logger, exclude_fields):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter(exclude_fields=exclude_fields))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("stack info!", stack_info=True)

    ecs = json.loads(stream.getvalue().rstrip())
    assert "error" not in ecs


def test_stdlibformatter_signature():
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {"my_formatter": {"class": "ecs_logging.StdlibFormatter"}},
        }
    )


def test_apm_data_conflicts(spec_validator):
    record = make_record()
    record.service = {"version": "1.0.0", "name": "myapp", "environment": "dev"}
    formatter = ecs_logging.StdlibFormatter(exclude_fields=["process"])

    assert spec_validator(formatter.format(record)) == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","log.level":"debug","message":"1: hello","ecs.version":"1.6.0",'
        '"log":{"logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},"function":"test_function"},'
        '"original":"1: hello"},"service":{"environment":"dev","name":"myapp","version":"1.0.0"}}'
    )


def test_ensure_ascii_default():
    """Test that ensure_ascii defaults to True (escaping non-ASCII characters)"""
    record = make_record()
    record.msg = "Hello 世界"
    record.args = ()

    formatter = ecs_logging.StdlibFormatter(exclude_fields=["process"])
    result = formatter.format(record)

    # With ensure_ascii=True (default), non-ASCII characters should be escaped
    assert "\\u4e16\\u754c" in result
    assert "世界" not in result

    # Verify the JSON is valid
    parsed = json.loads(result)
    assert parsed["message"] == "Hello 世界"


def test_ensure_ascii_true():
    """Test that ensure_ascii=True escapes non-ASCII characters"""
    record = make_record()
    record.msg = "Café ☕"
    record.args = ()

    formatter = ecs_logging.StdlibFormatter(
        exclude_fields=["process"], ensure_ascii=True
    )
    result = formatter.format(record)

    # With ensure_ascii=True, non-ASCII characters should be escaped
    assert "\\u00e9" in result  # é is escaped
    assert "\\u2615" in result  # ☕ is escaped
    assert "Café" not in result
    assert "☕" not in result

    # Verify the JSON is valid and correctly decoded
    parsed = json.loads(result)
    assert parsed["message"] == "Café ☕"


def test_ensure_ascii_false():
    """Test that ensure_ascii=False preserves non-ASCII characters"""
    record = make_record()
    record.msg = "Hello 世界"
    record.args = ()

    formatter = ecs_logging.StdlibFormatter(
        exclude_fields=["process"], ensure_ascii=False
    )
    result = formatter.format(record)

    # With ensure_ascii=False, non-ASCII characters should be preserved
    assert "世界" in result
    assert "\\u4e16" not in result

    # Verify the JSON is valid
    parsed = json.loads(result)
    assert parsed["message"] == "Hello 世界"


def test_ensure_ascii_false_with_emoji():
    """Test that ensure_ascii=False preserves emoji and special characters"""
    record = make_record()
    record.msg = "Café ☕ 你好"
    record.args = ()

    formatter = ecs_logging.StdlibFormatter(
        exclude_fields=["process"], ensure_ascii=False
    )
    result = formatter.format(record)

    # With ensure_ascii=False, all non-ASCII characters should be preserved
    assert "Café" in result
    assert "☕" in result
    assert "你好" in result

    # Verify the JSON is valid and correctly decoded
    parsed = json.loads(result)
    assert parsed["message"] == "Café ☕ 你好"


def test_ensure_ascii_with_extra_fields():
    """Test that ensure_ascii works with extra fields containing non-ASCII"""
    record = make_record()
    record.msg = "Test message"
    record.args = ()

    formatter = ecs_logging.StdlibFormatter(
        exclude_fields=["process"],
        ensure_ascii=False,
        extra={"user": "用户", "city": "北京"},
    )
    result = formatter.format(record)

    # With ensure_ascii=False, non-ASCII in extra fields should be preserved
    assert "用户" in result
    assert "北京" in result

    # Verify the JSON is valid
    parsed = json.loads(result)
    assert parsed["user"] == "用户"
    assert parsed["city"] == "北京"
