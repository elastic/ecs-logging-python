import logging
import mock
import pytest
import json
import time
import random
import ecs_logging
from .compat import StringIO


@pytest.fixture(scope="function")
def logger():
    return logging.getLogger("test-logger-%f-%f" % (time.time(), random.random()))


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


def test_record_formatted():
    formatter = ecs_logging.StdlibFormatter(exclude_fields=["process"])

    assert formatter.format(make_record()) == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","ecs":{"version":"1.5.0"},'
        '"log":{"level":"debug","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
        '"function":"test_function"},"original":"1: hello"},"message":"1: hello"}'
    )


def test_can_be_overridden():
    class CustomFormatter(ecs_logging.StdlibFormatter):
        def format_to_ecs(self, record):
            ecs_dict = super(CustomFormatter, self).format_to_ecs(record)
            ecs_dict["custom"] = "field"
            return ecs_dict

    formatter = CustomFormatter(exclude_fields=["process"])
    assert formatter.format(make_record()) == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","custom":"field","ecs":{"version":"1.5.0"},'
        '"log":{"level":"debug","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
        '"function":"test_function"},"original":"1: hello"},"message":"1: hello"}'
    )


def test_can_be_set_on_handler():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter(exclude_fields=["process"]))

    handler.handle(make_record())

    assert stream.getvalue() == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","ecs":{"version":"1.5.0"},'
        '"log":{"level":"debug","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
        '"function":"test_function"},"original":"1: hello"},"message":"1: hello"}\n'
    )


@mock.patch("time.time")
def test_extra_is_merged(time, logger):
    time.return_value = 1584720997.187709

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
        "ecs": {"version": "1.5.0"},
        "log": {
            "level": "info",
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
    assert ecs["log"]["level"] == "info"
    assert ecs["message"] == "there was an error"
    assert ecs["log"]["original"] == "there was an error"


def test_stack_trace_limit_traceback(logger):
    def f():
        g()

    def g():
        h()

    def h():
        raise ValueError("error!")

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter(stack_trace_limit=2))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        f()
    except ValueError:
        logger.info("there was an error", exc_info=True)

    ecs = json.loads(stream.getvalue().rstrip())
    error_stack_trace = ecs["error"].pop("stack_trace")
    assert all(x in error_stack_trace for x in ("f()", "g()"))
    assert "h()" not in error_stack_trace
    assert ecs["error"] == {
        "message": "error!",
        "type": "ValueError",
    }
    assert ecs["log"]["level"] == "info"
    assert ecs["message"] == "there was an error"
    assert ecs["log"]["original"] == "there was an error"


def test_stack_trace_limit_types_and_values():
    with pytest.raises(TypeError) as e:
        ecs_logging.StdlibFormatter(stack_trace_limit="a")
    assert str(e.value) == "'stack_trace_limit' must be None, or a non-negative integer"

    with pytest.raises(ValueError) as e:
        ecs_logging.StdlibFormatter(stack_trace_limit=-1)
    assert str(e.value) == "'stack_trace_limit' must be None, or a non-negative integer"


@pytest.mark.parametrize(
    "exclude_fields",
    [
        "process",
        "ecs",
        "ecs.version",
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
