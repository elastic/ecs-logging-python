# Changelog

## 2.2.0 (2024-06-28)

- Rewrite type annotations ([#119](https://github.com/elastic/ecs-logging-python/pull/119))
- Don't de-dot `ecs.version` ([#118](https://github.com/elastic/ecs-logging-python/pull/118))
- Make it possible override the JSON serializer in `StructlogFormatter` ([#114](https://github.com/elastic/ecs-logging-python/pull/114))
- Use `fromtimestamp` instead of deprecated `utcfromtimestamp` ([#105](https://github.com/elastic/ecs-logging-python/pull/105))
- Remove unused imports and fix an undefined name ([#101](https://github.com/elastic/ecs-logging-python/pull/101))

## 2.1.0 (2023-08-16)

- Add support for `service.environment` from APM log correlation ([#96](https://github.com/elastic/ecs-logging-python/pull/96))
- Fix stack trace handling in StructLog for ECS compliance ([#97](https://github.com/elastic/ecs-logging-python/pull/97))

## 2.0.2 (2023-05-17)

- Allow flit-core 3+ ([#94](https://github.com/elastic/ecs-logging-python/pull/94))
- Remove python2 leftovers ([#94](https://github.com/elastic/ecs-logging-python/pull/94))

## 2.0.0 (2022-05-18)

- Remove python 2 support ([#78](https://github.com/elastic/ecs-logging-python/pull/78))
- Add global `extra` context fields to `StdLibFormatter` ([#65](https://github.com/elastic/ecs-logging-python/pull/65))

## 1.1.0 (2021-10-18)

- Remove python 3.5 support ([#69](https://github.com/elastic/ecs-logging-python/pull/69))
- Fix an issue where APM fields would override user-provided fields even when
  APM wasn't installed ([#67](https://github.com/elastic/ecs-logging-python/pull/67))
- Removed `event.dataset` field handling to match
  [`elastic-apm` v6.6.0](https://github.com/elastic/apm-agent-python/releases/tag/v6.6.0)
  ([#69](https://github.com/elastic/ecs-logging-python/pull/69))

## 1.0.2 (2021-09-22)

- Fix an signature mismatch between `StdLibFormatter` and `logging.Formatter`,
  which could cause issues in Django and Gunicorn
  ([#54](https://github.com/elastic/ecs-logging-python/pull/54))

## 1.0.1 (2021-07-06)

- Fixed an issue in `StructlogFormatter` caused by a conflict with `event`
  (used for the log `message`) and `event.dataset` (a field provided by the
  `elasticapm` integration) ([#46](https://github.com/elastic/ecs-logging-python/pull/46))
- Add default/fallback handling for json.dumps ([#47](https://github.com/elastic/ecs-logging-python/pull/47))
- Fixed an issue in `StdLibFormatter` when `exc_info=False` ([#42](https://github.com/elastic/ecs-logging-python/pull/42))

## 1.0.0 (2021-02-08)

- Remove "beta" designation

## 0.6.0 (2021-01-21)

- Add validation against the ecs-logging [spec](https://github.com/elastic/ecs-logging/blob/main/spec/spec.json) ([#31](https://github.com/elastic/ecs-logging-python/pull/31))
- Add support for `service.name` from APM log correlation ([#32](https://github.com/elastic/ecs-logging-python/pull/32))
- Correctly order `@timestamp`, `log.level`, and `message` fields ([#28](https://github.com/elastic/ecs-logging-python/pull/28))

## 0.5.0 (2020-08-27)

- Updated supported ECS version to 1.6.0 ([#24](https://github.com/elastic/ecs-logging-python/pull/24))
- Added support for `LogRecord.stack_info` ([#23](https://github.com/elastic/ecs-logging-python/pull/23))
- Fixed normalizing of items in `list` that aren't of type
  `dict` ([#22](https://github.com/elastic/ecs-logging-python/pull/22), contributed by [`@camerondavison`](https://github.com/camerondavison))

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
