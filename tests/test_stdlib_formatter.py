import logging
import mock
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
        '"log":{"level":"debug","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
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
        '"log":{"level":"debug","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
        '"function":"test_function"},"original":"1: hello"},"message":"1: hello"}'
    )


def test_can_be_set_on_handler():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter())

    handler.handle(make_record())

    assert stream.getvalue() == (
        '{"@timestamp":"2020-03-20T14:12:46.123Z","ecs":{"version":"1.5.0"},'
        '"log":{"level":"debug","logger":"logger-name","origin":{"file":{"line":10,"name":"file.py"},'
        '"function":"test_function"},"original":"1: hello"},"message":"1: hello"}\n'
    )


@mock.patch("time.time")
def test_extra_is_merged(time):
    time.return_value = 1584720997.187709

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ecs_logging.StdlibFormatter())
    logger = logging.getLogger("test-logger")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("hey world", extra={"tls": {"cipher": "AES"}, "tls.established": True})

    assert stream.getvalue() == (
        '{"@timestamp":"2020-03-20T16:16:37.187Z","ecs":{"version":"1.5.0"},"log":'
        '{"level":"info","logger":"test-logger","origin":{"file":{"line":73,"name":'
        '"test_stdlib_formatter.py"},"function":"test_extra_is_merged"},"original":"hey '
        'world"},"message":"hey world","tls":{"cipher":"AES","established":true}}\n'
    )
