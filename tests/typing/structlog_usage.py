import sys
from typing import List, Tuple

import ecs_logging
import structlog
from structlog.typing import Processor


shared_processors: Tuple[Processor, ...] = (
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
)

processors: List[Processor]
if sys.stderr.isatty():
    processors = [
        *shared_processors,
        structlog.dev.ConsoleRenderer(),
    ]
else:
    processors = [
        *shared_processors,
        structlog.processors.dict_tracebacks,
        ecs_logging.StructlogFormatter(),
    ]

structlog.configure(
    processors=processors,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
