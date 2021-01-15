# ecs-logging-python

[![Build Status](https://apm-ci.elastic.co/job/apm-agent-python/job/ecs-logging-python-mbp/job/master/badge/icon)](https://apm-ci.elastic.co/blue/organizations/jenkins/apm-agent-python%2Fecs-logging-python-mbp/branches)
[![PyPI](https://img.shields.io/pypi/v/ecs-logging)](https://pypi.org/project/ecs-logging)
[![Versions Supported](https://img.shields.io/pypi/pyversions/ecs-logging)](https://pypi.org/project/ecs-logging)

**Please note** that this is library is in a **beta** version and backwards-incompatible
changes might be introduced in future releases. While we strive to comply to
[semver](https://semver.org), we can not guarantee to avoid breaking changes in minor releases.

Check out the [Elastic Common Schema (ECS) reference](https://www.elastic.co/guide/en/ecs/current/index.html)
for more information.

The library currently implements ECS 1.6, after a 1.x version is released
we will be following (ECS.major).(ECS.minor).(package minor) as our versioning scheme.

## Installation

```console
$ python -m pip install ecs-logging
```

## Documentation

See the [ECS Logging Python reference](https://www.elastic.co/guide/en/ecs-logging/python/current/index.html) on elastic.co to get started.

## Elastic APM Log Correlation

`ecs-logging-python` supports automatically collecting [ECS tracing fields](https://www.elastic.co/guide/en/ecs/master/ecs-tracing.html)
from the [Elastic APM Python agent](https://github.com/elastic/apm-agent-python) in order to
[correlate logs to spans, transactions and traces](https://www.elastic.co/guide/en/apm/agent/python/current/log-correlation.html) in Elastic APM.

## License

Apache-2.0
