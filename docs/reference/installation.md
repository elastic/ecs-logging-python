---
mapped_pages:
  - https://www.elastic.co/guide/en/ecs-logging/python/current/installation.html
navigation_title: Installation
---

# ECS Logging Python installation [installation]

```cmd
$ python -m pip install ecs-logging
```


## Getting started [gettingstarted]

`ecs-logging-python` has formatters for the standard library [`logging`](https://docs.python.org/3/library/logging.html) module and the [`structlog`](https://www.structlog.org/en/stable/) package.


### Standard library logging module [logging]

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
logger.debug("Example message!", extra={"http.request.method": "get"})
```

```json
{
    "@timestamp": "2020-03-20T18:11:37.895Z",
    "log.level": "debug",
    "message": "Example message!",
    "ecs": {
        "version": "1.6.0"
    },
    "http": {
      "request": {
        "method": "get"
      }
    },
    "log": {
        "logger": "app",
        "origin": {
            "file": {
                "line": 14,
                "name": "test.py"
            },
            "function": "func"
        },
        "original": "Example message!"
    }
}
```


#### Excluding fields [_excluding_fields]

You can exclude fields from being collected by using the `exclude_fields` option in the `StdlibFormatter` constructor:

```python
from ecs_logging import StdlibFormatter

formatter = StdlibFormatter(
    exclude_fields=[
        # You can specify individual fields to ignore:
        "log.original",
        # or you can also use prefixes to ignore
        # whole categories of fields:
        "process",
        "log.origin",
    ]
)
```


#### Limiting stack traces [_limiting_stack_traces]

The `StdlibLogger` automatically gathers `exc_info` into ECS `error.*` fields. If you’d like to control the number of stack frames that are included in `error.stack_trace` you can use the `stack_trace_limit` parameter (by default all frames are collected):

```python
from ecs_logging import StdlibFormatter

formatter = StdlibFormatter(
    # Only collects 3 stack frames
    stack_trace_limit=3,
)
formatter = StdlibFormatter(
    # Disable stack trace collection
    stack_trace_limit=0,
)
```


#### Controlling ASCII encoding [_controlling_ascii_encoding]

```{applies_to}
product: ga 2.3.0
```

By default, the `StdlibFormatter` escapes non-ASCII characters in the JSON output using Unicode escape sequences. If you want to preserve non-ASCII characters (such as Chinese, Japanese, emojis, etc.) in their original form, you can use the `ensure_ascii` parameter:

```python
from ecs_logging import StdlibFormatter

# Default behavior - non-ASCII characters are escaped
formatter = StdlibFormatter()
# Output: {"message":"Hello \\u4e16\\u754c"}

# Preserve non-ASCII characters
formatter = StdlibFormatter(ensure_ascii=False)
# Output: {"message":"Hello 世界"}
```

This is particularly useful when working with internationalized applications or when you need to maintain readability of logs containing non-ASCII characters.


### Structlog Example [structlog]

Note that the structlog processor should be the last processor in the list, as it handles the conversion to JSON as well as the ECS field enrichment.

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


#### Controlling ASCII encoding for Structlog [_structlog_ascii_encoding]

```{applies_to}
product: ga 2.3.0
```

Similar to `StdlibFormatter`, the `StructlogFormatter` also supports the `ensure_ascii` parameter to control whether non-ASCII characters are escaped:

```python
import structlog
import ecs_logging

# Configure Structlog with ensure_ascii=False to preserve non-ASCII characters
structlog.configure(
    processors=[ecs_logging.StructlogFormatter(ensure_ascii=False)],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger("app")
logger.info("你好世界")  # Non-ASCII characters will be preserved in output
```

```json
{
  "@timestamp": "2020-03-26T13:08:11.728Z",
  "ecs": {
    "version": "1.6.0"
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


## Elastic APM log correlation [correlation]

`ecs-logging-python` supports automatically collecting  [ECS tracing fields](ecs://reference/ecs-tracing.md) from the [Elastic APM Python agent](https://github.com/elastic/apm-agent-python) in order to [correlate logs to spans, transactions and traces](apm-agent-python://reference/logs.md) in Elastic APM.

You can also quickly turn on ECS-formatted logs in your python app by setting [`LOG_ECS_REFORMATTING=override`](apm-agent-python://reference/configuration.md#config-log_ecs_reformatting) in the Elastic APM Python agent.


## Install Filebeat [filebeat]

The best way to collect the logs once they are ECS-formatted is with [Filebeat](https://www.elastic.co/beats/filebeat):

:::::::{tab-set}

::::::{tab-item} Log file
1. Follow the [Filebeat quick start](beats://reference/filebeat/filebeat-installation-configuration.md)
2. Add the following configuration to your `filebeat.yaml` file.

For Filebeat 7.16+

```yaml
filebeat.inputs:
- type: filestream <1>
  paths: /path/to/logs.json
  parsers:
    - ndjson:
      overwrite_keys: true <2>
      add_error_key: true <3>
      expand_keys: true <4>

processors: <5>
  - add_host_metadata: ~
  - add_cloud_metadata: ~
  - add_docker_metadata: ~
  - add_kubernetes_metadata: ~
```

1. Use the filestream input to read lines from active log files.
2. Values from the decoded JSON object overwrite the fields that {{filebeat}} normally adds (type, source, offset, etc.) in case of conflicts.
3. {{filebeat}} adds an "error.message" and "error.type: json" key in case of JSON unmarshalling errors.
4. {{filebeat}} will recursively de-dot keys in the decoded JSON, and expand them into a hierarchical object structure.
5. Processors enhance your data. See [processors](beats://reference/filebeat/filtering-enhancing-data.md) to learn more.


For Filebeat < 7.16

```yaml
filebeat.inputs:
- type: log
  paths: /path/to/logs.json
  json.keys_under_root: true
  json.overwrite_keys: true
  json.add_error_key: true
  json.expand_keys: true

processors:
- add_host_metadata: ~
- add_cloud_metadata: ~
- add_docker_metadata: ~
- add_kubernetes_metadata: ~
```
::::::

::::::{tab-item} Kubernetes
1. Make sure your application logs to stdout/stderr.
2. Follow the [Run Filebeat on Kubernetes](beats://reference/filebeat/running-on-kubernetes.md) guide.
3. Enable [hints-based autodiscover](beats://reference/filebeat/configuration-autodiscover-hints.md) (uncomment the corresponding section in `filebeat-kubernetes.yaml`).
4. Add these annotations to your pods that log using ECS loggers. This will make sure the logs are parsed appropriately.

```yaml
annotations:
  co.elastic.logs/json.overwrite_keys: true <1>
  co.elastic.logs/json.add_error_key: true <2>
  co.elastic.logs/json.expand_keys: true <3>
```

1. Values from the decoded JSON object overwrite the fields that {{filebeat}} normally adds (type, source, offset, etc.) in case of conflicts.
2. {{filebeat}} adds an "error.message" and "error.type: json" key in case of JSON unmarshalling errors.
3. {{filebeat}} will recursively de-dot keys in the decoded JSON, and expand them into a hierarchical object structure.
::::::

::::::{tab-item} Docker
1. Make sure your application logs to stdout/stderr.
2. Follow the [Run Filebeat on Docker](beats://reference/filebeat/running-on-docker.md) guide.
3. Enable [hints-based autodiscover](beats://reference/filebeat/configuration-autodiscover-hints.md).
4. Add these labels to your containers that log using ECS loggers. This will make sure the logs are parsed appropriately.

```yaml
labels:
  co.elastic.logs/json.overwrite_keys: true <1>
  co.elastic.logs/json.add_error_key: true <2>
  co.elastic.logs/json.expand_keys: true <3>
```

1. Values from the decoded JSON object overwrite the fields that {{filebeat}} normally adds (type, source, offset, etc.) in case of conflicts.
2. {{filebeat}} adds an "error.message" and "error.type: json" key in case of JSON unmarshalling errors.
3. {{filebeat}} will recursively de-dot keys in the decoded JSON, and expand them into a hierarchical object structure.
::::::

:::::::
For more information, see the [Filebeat reference](beats://reference/filebeat/configuring-howto-filebeat.md).

