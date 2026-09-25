import pathlib
import subprocess
import sys

import pytest

_THIS_DIR = pathlib.Path(__file__).parent


@pytest.mark.parametrize("file", list((_THIS_DIR / "typing").glob("*.py")))
@pytest.mark.xfail(
    sys.version_info < (3, 10),
    reason="Older versions of mypy hit https://github.com/python/mypy/issues/16947 on StdlibFormatter.converter",
)
def test_type_check(file):
    subprocess.check_call(
        [sys.executable, "-m", "mypy", "--strict", "--config-file=", file]
    )
