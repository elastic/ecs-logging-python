# ecs-logging-python

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

```python
>>> import logging
>>> import ecs_logging

# Get the Logger
>>> logger = logging.getLogger("app")
>>> logger.setLevel(logging.DEBUG)

# Add an ECS formatter to the Handler
>>> handler = logging.StreamHandler()
>>> handler.setFormatter(ecs_logging.StdlibFormatter())
>>> logger.addHandler(handler)

# Emit a log! :)
>>> logger.debug("Example message!")
{"@timestamp":"2020-03-17T16:28:51.353Z","ecs":{"version":"1.0.0"}...
```

## License

Apache-2.0
