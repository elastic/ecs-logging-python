"""Logging formatters for ECS (Elastic Common Schema) in Python"""

from ._meta import ECS_VERSION
from ._stdlib import StdlibFormatter
from ._structlog import StructlogFormatter

__version__ = "0.4"
__all__ = [
    "ECS_VERSION",
    "StdlibFormatter",
    "StructlogFormatter",
]
