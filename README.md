# ecs-logging-python

[![Build Status](https://github.com/elastic/ecs-logging-python/actions/workflows/test.yml/badge.svg)](https://github.com/elastic/ecs-logging-pythonactions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/ecs-logging)](https://pypi.org/project/ecs-logging)
[![Versions Supported](https://img.shields.io/pypi/pyversions/ecs-logging)](https://pypi.org/project/ecs-logging)

Check out the [Elastic Common Schema (ECS) reference](https://www.elastic.co/guide/en/ecs/current/index.html)
for more information.

The library currently implements ECS 1.6.

## Installation

```console
$ python -m pip install ecs-logging
```

## Documentation

See the [ECS Logging Python reference](https://www.elastic.co/guide/en/ecs-logging/python/current/index.html) on elastic.co to get started.

## Elastic APM Log Correlation

`ecs-logging-python` supports automatically collecting [ECS tracing fields](https://www.elastic.co/guide/en/ecs/current/ecs-tracing.html)
from the [Elastic APM Python agent](https://github.com/elastic/apm-agent-python) in order to
[correlate logs to spans, transactions and traces](https://www.elastic.co/guide/en/apm/agent/python/current/log-correlation.html) in Elastic APM.

## License

Apache-2.0
