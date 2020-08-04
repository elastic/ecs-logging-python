# Changelog

## 0.4 (2020-08-04)

- Added automatic collection of ECS fields `trace.id`, `span.id`, and `transaction.id` for
  [Log Correlation](https://www.elastic.co/guide/en/apm/agent/python/master/log-correlation.html) with
  the Python Elastic APM agent ([#17](https://github.com/elastic/ecs-logging-python/pull/17))

## 0.3 (2020-07-27)

- Added collecting `LogRecord.exc_info` into `error.*` fields
  automatically for `StdlibFormatter` ([#16](https://github.com/elastic/ecs-logging-python/pull/16))
- Added collecting process and thread info from `LogRecord` into `process.*` fields
  automatically for `StdlibFormatter` ([#16](https://github.com/elastic/ecs-logging-python/pull/16))
- Added `exclude_fields` parameter to `StdlibFormatter` to
  exclude fields from being formatted to JSON ([#16](https://github.com/elastic/ecs-logging-python/pull/16))
- Added `stack_trace_limit` parameter to `StdlibFormatter`
  to control the number of stack trace frames being
  formatted in `error.stack_trace` ([#16](https://github.com/elastic/ecs-logging-python/pull/16))

Thanks to community contributor Jon Moore ([@comcast-jonm](https://github.com/comcast-jonm))
for their contributions to this release.

## 0.2 (2020-04-28)

- Added support for using `log(..., extra={...})` on standard library
  loggers to use extended and custom fields ([#8](https://github.com/elastic/ecs-logging-python/pull/8))

## 0.1 (2020-03-26)

- Added `StdlibFormatter` for use with the standard library `logging` module
- Added `StructlogFormatter` for use with the `structlog` package
