import json
import sys
import elasticapm
from elasticapm.handlers.logging import LoggingFilter
from elasticapm.handlers.structlog import structlog_processor
import ecs_logging
import logging
import structlog
import pytest
from .compat import StringIO


def test_elasticapm_structlog_log_correlation_ecs_fields():
    apm = elasticapm.Client({"SERVICE_NAME": "apm-service", "DISABLE_SEND": True})
    stream = StringIO()
    logger = structlog.PrintLogger(stream)
    logger = structlog.wrap_logger(
        logger, processors=[structlog_processor, ecs_logging.StructlogFormatter()]
    )
    log = logger.new()

    apm.begin_transaction("test-transaction")
    try:
        with elasticapm.capture_span("test-span"):
            span_id = elasticapm.get_span_id()
            trace_id = elasticapm.get_trace_id()
            transaction_id = elasticapm.get_transaction_id()

            log.info("test message")
    finally:
        apm.end_transaction("test-transaction")

    ecs = json.loads(stream.getvalue().rstrip())
    ecs.pop("@timestamp")
    assert ecs == {
        "ecs": {"version": "1.5.0"},
        "log": {"level": "info"},
        "message": "test message",
        "span": {"id": span_id},
        "trace": {"id": trace_id},
        "transaction": {"id": transaction_id},
    }


@pytest.mark.skipif(
    sys.version_info < (3, 2), reason="elastic-apm uses logger factory in Python 3.2+"
)
def test_elastic_apm_stdlib_no_filter_log_correlation_ecs_fields():
    apm = elasticapm.Client({"SERVICE_NAME": "apm-service", "DISABLE_SEND": True})
    stream = StringIO()
    logger = logging.getLogger("apm-logger")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        ecs_logging.StdlibFormatter(
            exclude_fields=["@timestamp", "process", "log.origin.file.line"]
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    apm.begin_transaction("test-transaction")
    try:
        with elasticapm.capture_span("test-span"):
            span_id = elasticapm.get_span_id()
            trace_id = elasticapm.get_trace_id()
            transaction_id = elasticapm.get_transaction_id()

            logger.info("test message")
    finally:
        apm.end_transaction("test-transaction")

    ecs = json.loads(stream.getvalue().rstrip())
    assert ecs == {
        "ecs": {"version": "1.5.0"},
        "log": {
            "level": "info",
            "logger": "apm-logger",
            "origin": {
                "file": {"name": "test_apm.py"},
                "function": "test_elastic_apm_stdlib_no_filter_log_correlation_ecs_fields",
            },
            "original": "test message",
        },
        "message": "test message",
        "span": {"id": span_id},
        "trace": {"id": trace_id},
        "transaction": {"id": transaction_id},
    }


def test_elastic_apm_stdlib_with_filter_log_correlation_ecs_fields():
    apm = elasticapm.Client({"SERVICE_NAME": "apm-service", "DISABLE_SEND": True})
    stream = StringIO()
    logger = logging.getLogger("apm-logger")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        ecs_logging.StdlibFormatter(
            exclude_fields=["@timestamp", "process", "log.origin.file.line"]
        )
    )
    handler.addFilter(LoggingFilter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    apm.begin_transaction("test-transaction")
    try:
        with elasticapm.capture_span("test-span"):
            span_id = elasticapm.get_span_id()
            trace_id = elasticapm.get_trace_id()
            transaction_id = elasticapm.get_transaction_id()

            logger.info("test message")
    finally:
        apm.end_transaction("test-transaction")

    ecs = json.loads(stream.getvalue().rstrip())
    assert ecs == {
        "ecs": {"version": "1.5.0"},
        "log": {
            "level": "info",
            "logger": "apm-logger",
            "origin": {
                "file": {"name": "test_apm.py"},
                "function": "test_elastic_apm_stdlib_with_filter_log_correlation_ecs_fields",
            },
            "original": "test message",
        },
        "message": "test message",
        "span": {"id": span_id},
        "trace": {"id": trace_id},
        "transaction": {"id": transaction_id},
    }


def test_elastic_apm_stdlib_exclude_fields():
    apm = elasticapm.Client({"SERVICE_NAME": "apm-service", "DISABLE_SEND": True})
    stream = StringIO()
    logger = logging.getLogger("apm-logger")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        ecs_logging.StdlibFormatter(
            exclude_fields=[
                "@timestamp",
                "process",
                "log.origin.file.line",
                "span",
                "transaction.id",
            ]
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    apm.begin_transaction("test-transaction")
    try:
        with elasticapm.capture_span("test-span"):
            trace_id = elasticapm.get_trace_id()

            logger.info("test message")
    finally:
        apm.end_transaction("test-transaction")

    ecs = json.loads(stream.getvalue().rstrip())
    assert ecs == {
        "ecs": {"version": "1.5.0"},
        "log": {
            "level": "info",
            "logger": "apm-logger",
            "origin": {
                "file": {"name": "test_apm.py"},
                "function": "test_elastic_apm_stdlib_exclude_fields",
            },
            "original": "test message",
        },
        "message": "test message",
        "trace": {"id": trace_id},
    }
