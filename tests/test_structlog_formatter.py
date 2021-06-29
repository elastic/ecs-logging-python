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

import ecs_logging
import structlog
import mock
from .compat import StringIO


class NotSerializable:
    def __repr__(self):
        return "<NotSerializable>"


def make_event_dict():
    return {
        "event": "test message",
        "log.logger": "logger-name",
        "baz": NotSerializable(),
    }


@mock.patch("time.time")
def test_event_dict_formatted(time, spec_validator):
    time.return_value = 1584720997.187709

    formatter = ecs_logging.StructlogFormatter()
    assert spec_validator(formatter(None, "debug", make_event_dict())) == (
        '{"@timestamp":"2020-03-20T16:16:37.187Z","log.level":"debug",'
        '"message":"test message",'
        '"baz":"<NotSerializable>",'
        '"ecs":{"version":"1.6.0"},'
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
        '"ecs":{"version":"1.6.0"}}\n'
    )
