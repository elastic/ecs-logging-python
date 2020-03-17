# ecs-logging-python

Please note that this is library is in a beta version and backwards-incompatible
changes might be introduced in future releases.

## Installation

```console
python -m pip install ecs-logging
```

## Getting Started

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

# Emit a log! :)
logger.debug("Example message!")
```

## License

Apache-2.0
