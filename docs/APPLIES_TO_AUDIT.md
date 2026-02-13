# applies_to tags audit

Per the [Docs Versioning contributor guidelines](https://www.elastic.co/docs/contribute-docs/how-to/cumulative-docs) and [docs-builder applies_to syntax](https://elastic.github.io/docs-builder/syntax/applies/):

- **Page-level frontmatter is mandatory**: every doc page referenced in the TOC must include an `applies_to` block in YAML frontmatter.
- The `products` frontmatter is used by the Search UI to filter results; including it is recommended.

## Where applies_to is missing

| File | Status | Notes |
|------|--------|--------|
| `docs/reference/index.md` | **Missing** | Frontmatter has only `mapped_pages`. No `applies_to` or `products`. |
| `docs/reference/installation.md` | **Missing** | Frontmatter has `mapped_pages` and `navigation_title`. No page-level `applies_to` or `products`. Has section-level `{applies_to}` for two subsections (Controlling ASCII encoding, Structlog ASCII encoding) — those are correct. |

## Context from other repos

- **ecs-logging-nodejs** and **ecs-logging-go-zerolog**: Use `applies_to: stack: ga`, `serverless: ga` and `products: - id: ecs-logging` (go-zerolog also has `elastic-stack`) in every reference page frontmatter.
- **docs-content**: Pages consistently use `applies_to` + `products` in frontmatter; stack/serverless/deployment/product keys depend on the doc’s scope.
- **Contributor guidelines**: For “product following its own versioning schema” the example is `product: ga` and a products list. For docs primarily about using Stack components or serverless UI, use `stack: ga` and `serverless: ga`.

ECS Logging Python is used with the Elastic Stack and Serverless when logging from an app, so the same pattern as the other ECS logging language repos is appropriate: **stack + serverless** in `applies_to`, plus **products** for search.

## Section-level applies_to (already present)

`installation.md` correctly uses section-level `{applies_to}` where content differs from the page default:

- **Controlling ASCII encoding** (`_controlling_ascii_encoding`): `product: ga 2.3.0`
- **Controlling ASCII encoding for Structlog** (`_structlog_ascii_encoding`): `product: ga 2.3.0`

No other sections in the current docs need section-level applies_to.

## Recommendation

Add to **both** `docs/reference/index.md` and `docs/reference/installation.md` frontmatter:

```yaml
applies_to:
  stack: ga
  serverless: ga
products:
  - id: ecs-logging
```

Keep existing keys (`mapped_pages`, `navigation_title` where present). Order in frontmatter is flexible; other repos often put `applies_to` and `products` after `mapped_pages` / `navigation_title`.

---

## Content vs applies_to check

Page-level tags: `stack: ga`, `serverless: ga` (content applies to Elastic Stack and Serverless).

### docs/reference/index.md

| Section / content | Consistent with applies_to? | Notes |
|-------------------|----------------------------|--------|
| Intro (ECS loggers, formatter/encoder plugins) | ✓ | Generic; applies to both Stack and Serverless. |
| Tip (ECS logging guide link) | ✓ | Generic. |
| "Get started" link | ✓ | Generic. |
| Tutorial link (Ingest logs from Python app using Filebeat) | ✓ | Filebeat ingestion is used with both Stack and Serverless; no context change. |

**Verdict:** Content matches page-level `stack: ga`, `serverless: ga`. No section-level tags needed.

---

### docs/reference/installation.md

| Section / content | Consistent with applies_to? | Notes |
|-------------------|----------------------------|--------|
| Title, pip install | ✓ | Generic. |
| Getting started (StdlibFormatter, StructlogFormatter) | ✓ | Generic. |
| Standard library logging module (code example) | ✓ | Generic. |
| Excluding fields | ✓ | Generic. |
| Limiting stack traces | ✓ | Generic. |
| **Controlling ASCII encoding** | ✓ | Section-level `product: ga 2.3.0` correctly narrows to ecs-logging-python 2.3.0+ for `ensure_ascii`. |
| Structlog Example | ✓ | Generic. |
| **Controlling ASCII encoding for Structlog** | ✓ | Section-level `product: ga 2.3.0` correct. |
| **Elastic APM log correlation** | ✓ | APM is available on both Stack and Serverless; page-level tags are correct. |
| **Install Filebeat** (Log file, Kubernetes, Docker tabs) | ✓ | Filebeat is used with Stack and can ship to Serverless; no context change. |
| Filebeat 7.16+ vs Filebeat &lt; 7.16 config blocks | Optional | Content is version-specific (filestream/ndjson vs log/json.*). Other ECS logging repos (nodejs, go-zerolog, ecs-dotnet, etc.) do not add section-level `applies_to` for this split; the headings make the version clear. Adding e.g. `stack: ga 7.16` for the 7.16+ block would be consistent with cumulative docs but is not required for consistency with sibling repos. |

**Verdict:** All content is consistent with the page-level and existing section-level tags. No mandatory changes. Optionally, the Filebeat 7.16+ block could be tagged with `stack: ga 7.16` if you want version badges for that variant.
