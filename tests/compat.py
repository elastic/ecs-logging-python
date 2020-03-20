import sys

if sys.version_info >= (3,):
    from io import StringIO
else:
    from io import BytesIO as StringIO

__all__ = ["StringIO"]
