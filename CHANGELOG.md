# Changelog

## 0.2 (2020-04-28)

- Added support for using `log(..., extra={...})` on standard library
  loggers to use extended and custom fields ([#8](https://github.com/elastic/ecs-logging-python/pull/8))

## 0.1 (2020-03-26)

- Added `StdlibFormatter` for use with the standard library `logging` module
- Added `StructlogFormatter` for use with the `structlog` package
