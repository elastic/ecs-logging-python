# ecs-logging-python

[![Build Status](https://apm-ci.elastic.co/job/apm-agent-python/job/ecs-logging-python-mbp/job/master/badge/icon)](https://apm-ci.elastic.co/blue/organizations/jenkins/apm-agent-python%2Fecs-logging-python-mbp/branches)
[![PyPI](https://img.shields.io/pypi/v/ecs-logging)](https://pypi.org/project/ecs-logging)
[![Versions Supported](https://img.shields.io/pypi/pyversions/ecs-logging)](https://pypi.org/project/ecs-logging)

**Please note** that this is library is in a **beta** version and backwards-incompatible
changes might be introduced in future releases. While we strive to comply to
[semver](https://semver.org), we can not guarantee to avoid breaking changes in minor releases.

Check out the [Elastic Common Schema (ECS) reference](https://www.elastic.co/guide/en/ecs/current/index.html)
for more information.

The library currently implements ECS 1.5, after a 1.x version is released
we will be following (ECS.major).(ECS.minor).(package minor) as our versioning scheme.

## Installation

```console
python -m pip install ecs-logging
```

## Getting Started

`ecs-logging-python` has formatters for the standard library
[`logging`](https://docs.python.org/3/library/logging.html) module
and the [`structlog`](https://www.structlog.org/en/stable/) package.

### Logging Example

```python
import logging
import ecs_logging

# Get the Logger
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

# Add an ECS formatter to the Handler
handler = logging.StreamHandler()
handler.setFormatter(ecs_logging.StdlibFormatter())
logger.addHandler(handler)

# Emit a log!
logger.debug("Example message!")
```
```json
{
    "@timestamp": "2020-03-20T18:11:37.895Z",
    "ecs": {
        "version": "1.5.0"
    },
    "log": {
        "level": "DEBUG",
        "logger": "app",
        "origin": {
            "file": {
                "line": 14,
                "name": "test.py"
            },
            "function": "func"
        },
        "original": "Example message!"
    },
    "message": "Example message!"
}
```

### Structlog Example

```python
import structlog
import ecs_logging

# Configure Structlog
structlog.configure(
    processors=[ecs_logging.StructlogFormatter()],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# Get the Logger
logger = structlog.get_logger("app")

# Add additional context
logger = logger.bind(**{
    "http": {
        "version": "2",
        "request": {
            "method": "get",
            "bytes": 1337,
        },
    },
    "url": {
        "domain": "example.com",
        "path": "/",
        "port": 443,
        "scheme": "https",
        "registered_domain": "example.com",
        "top_level_domain": "com",
        "original": "https://example.com",
    }
})

# Emit a log!
logger.debug("Example message!")
```
```json
{
  "@timestamp": "2020-03-26T13:08:11.728Z",
  "ecs": {
    "version": "1.5.0"
  },
  "http": {
    "request": {
      "bytes": 1337,
      "method": "get"
    },
    "version": "2"
  },
  "log": {
    "level": "debug"
  },
  "message": "Example message!",
  "url": {
    "domain": "example.com",
    "original": "https://example.com",
    "path": "/",
    "port": 443,
    "registered_domain": "example.com",
    "scheme": "https",
    "top_level_domain": "com"
  }
}
```

## License

Apache-2.0
