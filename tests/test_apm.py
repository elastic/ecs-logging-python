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


def test_elasticapm_structlog_log_correlation_ecs_fields(spec_validator, apm):
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

    ecs = json.loads(spec_validator(stream.getvalue().rstrip()))
    ecs.pop("@timestamp")
    assert ecs == {
        "ecs": {"version": "1.6.0"},
        "log.level": "info",
        "message": "test message",
        "span": {"id": span_id},
        "trace": {"id": trace_id},
        "transaction": {"id": transaction_id},
        "service": {"name": "apm-service"},
        "event": {"dataset": "apm-service.log"},
    }


def test_elastic_apm_stdlib_no_filter_log_correlation_ecs_fields(apm):
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
        "ecs": {"version": "1.6.0"},
        "log.level": "info",
        "log": {
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
        "service": {"name": "apm-service"},
        "event": {"dataset": "apm-service.log"},
    }


def test_elastic_apm_stdlib_with_filter_log_correlation_ecs_fields(apm):
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
        "ecs": {"version": "1.6.0"},
        "log.level": "info",
        "log": {
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
        "service": {"name": "apm-service"},
        "event": {"dataset": "apm-service.log"},
    }


def test_elastic_apm_stdlib_exclude_fields(apm):
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
        "ecs": {"version": "1.6.0"},
        "log.level": "info",
        "log": {
            "logger": "apm-logger",
            "origin": {
                "file": {"name": "test_apm.py"},
                "function": "test_elastic_apm_stdlib_exclude_fields",
            },
            "original": "test message",
        },
        "message": "test message",
        "trace": {"id": trace_id},
        "service": {"name": "apm-service"},
        "event": {"dataset": "apm-service.log"},
    }
