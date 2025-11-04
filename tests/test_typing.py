import pathlib
import subprocess
import sys

import pytest

_THIS_DIR = pathlib.Path(__file__).parent


@pytest.mark.parametrize("file", (_THIS_DIR / "typing").glob("*.py"))
def test_type_check(file):
    subprocess.check_call(
        [sys.executable, "-m", "mypy", "--strict", "--config-file=", file]
    )
