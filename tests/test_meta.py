import re
from ecs_logging import ECS_VERSION


def test_ecs_version_format():
    assert re.match(r"[0-9](?:[.0-9]*[0-9])?", ECS_VERSION)
