import ecs_logging
import structlog
import mock
from .compat import StringIO


def make_event_dict():
    return {"event": "test message", "log.logger": "logger-name"}


@mock.patch("time.time")
def test_event_dict_formatted(time):
    time.return_value = 1584720997.187709

    formatter = ecs_logging.StructlogFormatter()
    assert formatter(None, "debug", make_event_dict()) == (
        '{"@timestamp":"2020-03-20T16:16:37.187Z","ecs":{"version":"1.5.0"},'
        '"log":{"level":"debug","logger":"logger-name"},"message":"test message"}'
    )


@mock.patch("time.time")
def test_can_be_set_as_processor(time):
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

    assert stream.getvalue() == (
        '{"@timestamp":"2020-03-20T16:16:37.187Z","custom":"key",'
        '"dot":{"ted":1},"ecs":{"version":"1.5.0"},"log":{"level":"debug"},'
        '"message":"test message"}\n'
    )
