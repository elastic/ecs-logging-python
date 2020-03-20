import logging
import ecs_logging
from .compat import StringIO


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
    formatter = ecs_logging.StdlibFormatter()

    assert formatter.format(make_record()) == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","ecs":{"version":"1.5.0"},'
        '"log":{"level":"DEBUG","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
        '"function":"test_function"},"original":"1: hello"},"message":"1: hello"}'
    )


def test_can_be_overridden():
    class CustomFormatter(ecs_logging.StdlibFormatter):
        def format_to_ecs(self, record):
            ecs_dict = super(CustomFormatter, self).format_to_ecs(record)
            ecs_dict["custom"] = "field"
            return ecs_dict

    formatter = CustomFormatter()
    assert formatter.format(make_record()) == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","custom":"field","ecs":{"version":"1.5.0"},'
        '"log":{"level":"DEBUG","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
        '"function":"test_function"},"original":"1: hello"},"message":"1: hello"}'
    )


def test_can_be_set_on_handler():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter())

    handler.handle(make_record())

    assert stream.getvalue() == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","ecs":{"version":"1.5.0"},'
        '"log":{"level":"DEBUG","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
        '"function":"test_function"},"original":"1: hello"},"message":"1: hello"}\n'
    )
