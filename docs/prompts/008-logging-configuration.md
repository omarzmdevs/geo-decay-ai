# Handoff 008 · Logging Configuration

## Objective

Every process configures logging once at start-up from the centralised
settings, so that the project's own records and those of its libraries reach
the same stream in the same format.

## Role

developer

## Tier

`TIER_LIGHT` — declarative configuration against a documented decision, no
design latitude and no business logic.

## Context

Sprint 2, second of two handoffs. It depends on handoff 007, whose `Settings`
object already declares `GEO_DECAY_LOG_LEVEL` and `GEO_DECAY_LOG_FORMAT`
without acting on them. ADR-006 decides the strategy; this handoff only
implements it, and any deviation from it is a reason to stop and report rather
than to improvise.

## Files to Read

- `docs/architecture/adr/adr-006-logging-strategy.md`
- `src/geo_decay_delivery/config.py` (from handoff 007)

## Files to Create or Modify

- `src/geo_decay_delivery/logging_config.py`
- `tests/unit/delivery/test_logging_config.py`

## Out of Scope

- Changing `Settings` or `.env.example`. If a setting is missing, stop and
  report; do not add it here.
- Any call to `configure_logging` from a module other than a test. There is no
  entry point yet; Sprints 20 and 21 will call it.
- Adding log statements anywhere in `src/`. This handoff configures logging; it
  does not instrument code.
- structlog, loguru, a project-specific `get_logger` wrapper, file handlers,
  rotation, or any new dependency. ADR-006 rejects each of these explicitly.

## Specification

**`configure_logging(settings) -> None`** applies `logging.config.dictConfig`
built from the settings passed in. It takes the settings object as an
argument; it must not read the environment itself.

- Two formatters, selected by `GEO_DECAY_LOG_FORMAT`:
  - `text` — human-readable, one line: timestamp, level, logger name,
    message. The value is `text`, not `console`: handoff 007 declared and
    tested it that way and ADR-006 names no values, so this handoff follows
    the delivered configuration rather than renaming it.
  - `json` — one JSON object per line, with at least `timestamp`, `level`,
    `logger`, `message`, and the exception text when there is one. Built with
    the standard library; no dependency.
- One handler, on standard output. No file handler.
- The root logger takes its level from `GEO_DECAY_LOG_LEVEL`.
- A per-logger override map raises the floor for noisy third-party loggers to
  `WARNING`. Seed it with the libraries already foreseeable — `urllib3`,
  `botocore`, `matplotlib`, `PIL` — as a dictionary that later sprints extend,
  with a comment saying so.
- `disable_existing_loggers` is `False`, so loggers created at import time by
  libraries keep working.
- Calling the function twice is safe and does not duplicate handlers.
- Call sites elsewhere in the project use `logging.getLogger(__name__)` from
  the standard library. Nothing in this module is imported in order to log.

## Acceptance Tests

no — configuration against a decided design.

## Acceptance Criteria

1. `configure_logging` is importable from `geo_decay_delivery.logging_config`
   and takes the settings object as its only required argument.
2. With `GEO_DECAY_LOG_FORMAT=json`, a record emitted through
   `logging.getLogger("x")` reaches standard output as a single line that
   parses as JSON and carries `level`, `logger` and `message`.
3. With `GEO_DECAY_LOG_FORMAT=text`, the same record is not JSON and
   contains the logger name and the message.
4. The root logger's level matches `GEO_DECAY_LOG_LEVEL`.
5. `urllib3` is at `WARNING` or higher after configuration.
6. Calling `configure_logging` twice leaves exactly one handler on the root
   logger.
7. No module under `src/` imports `structlog` or `loguru`, and no file handler
   is configured.
8. The full ADR-005 gate passes.

## Verification Command

```bash
uv run python -c "
import io, json, logging, contextlib, os
os.environ.update({'GEO_DECAY_BBOX': '-3.7,40.4,-3.6,40.5', 'GEO_DECAY_BBOX_CRS': 'EPSG:4326',
                   'GEO_DECAY_LOG_LEVEL': 'INFO', 'GEO_DECAY_LOG_FORMAT': 'json'})
from geo_decay_delivery.config import Settings
from geo_decay_delivery.logging_config import configure_logging
s = Settings(); configure_logging(s); configure_logging(s)
assert len(logging.getLogger().handlers) == 1, logging.getLogger().handlers
assert logging.getLogger().level == logging.INFO
assert logging.getLogger('urllib3').getEffectiveLevel() >= logging.WARNING
buf = io.StringIO()
logging.getLogger().handlers[0].stream = buf
logging.getLogger('x').info('hello')
rec = json.loads(buf.getvalue().strip())
assert rec['level'] == 'INFO' and rec['logger'] == 'x' and rec['message'] == 'hello', rec
print('logging ok')
" \
  && ! grep -rEq 'structlog|loguru|FileHandler|RotatingFileHandler' src/ \
  && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest \
  && git status --short
```

## Launch Command

```bash
claude -p "ROLE: developer. Execute docs/prompts/008-logging-configuration.md" \
  --model haiku --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv run *)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

No `uv sync` or `uv lock`: this handoff adds no dependency.

## Restore Point

The commit that closes handoff 007. This handoff does not start before
handoff 007 is ACCEPTED and committed, because it consumes `Settings`.

`ea8296b` — the commit that closes handoff 007
(`docs(sprint-02): record handoff 007 accepted and close the RUFF-ISORT debt`).
Working tree clean at launch, verified by the launcher.

---

## Run Record

Date: 2026-10-17
Tool and model: `claude -p` headless, `--model haiku`,
`--permission-mode dontAsk`, with the allowlist in the launch command above.
Launched by the orchestrator from a clean working tree at `ea8296b`.
Outcome: completed.

The launching shell pipeline exited non-zero, but the agent run itself
finished: the non-zero status came from the launcher's own `tee`, which the
sandbox denied because the log path lay outside the repository. Two incidents
inside the run, both reported by the developer and neither affecting the
delivered files: its first gate run failed on one `ruff format` nit in its own
test file, which it fixed and re-ran; and one compound shell command was denied
by `dontAsk`, which it did not work around.

## Verification

Verdict: **ACCEPTED**

Files changed — exactly the two the handoff lists, both new and untracked:

| File | |
|---|---|
| `src/geo_decay_delivery/logging_config.py` | new, 72 lines |
| `tests/unit/delivery/test_logging_config.py` | new, 143 lines, 8 tests |

`git diff tests/acceptance/` is empty, and `Settings`, `.env.example`,
`pyproject.toml` and `uv.lock` are untouched: the out-of-scope list holds, and
the handoff added no dependency.

Gate, re-run by the orchestrator: the handoff's verification command prints
`logging ok`; the grep finds no `structlog`, `loguru` or file handler in
`src/`; `ruff check` all checks passed; `ruff format --check` 17 files already
formatted; `mypy` success on 17 source files; `lint-imports` 4 contracts kept;
`pytest` **175 passed**, the 8 new ones among them.

Criteria, checked one by one:

1. `configure_logging` imports from `geo_decay_delivery.logging_config` and
   takes the settings object as its only argument. ✔
2. With `GEO_DECAY_LOG_FORMAT=json` the record reaches standard output as one
   line carrying `level`, `logger`, `message` and `timestamp`. ✔
3. With `text` the same record does not parse as JSON and contains the logger
   name and the message. ✔
4. The root logger's level matches `GEO_DECAY_LOG_LEVEL`. ✔
5. `urllib3` is at `WARNING` or higher after configuration. ✔
6. Two calls leave exactly one handler on the root logger. ✔
7. No `structlog`, `loguru` or file handler anywhere under `src/`. ✔
8. The full ADR-005 gate passes. ✔

Notes:

- **The noisy-logger map sets a level, it does not raise a floor.** With the
  root at `DEBUG` or `INFO` it behaves as the specification intends: `urllib3`,
  `botocore`, `matplotlib` and `PIL` stay at `WARNING`. With the root above
  `WARNING` the same entries let those libraries through while the project's
  own records are filtered, because a logger's own level, not the root's,
  decides. The handoff's criterion is met and the case is remote — the root sits
  at `ERROR` only if someone sets it there — so this is recorded as a known
  behaviour rather than a defect, for the sprint that adds an entry point to
  revisit.
- Idempotency comes from `dictConfig` replacing the handlers it installed, not
  from a guard flag, which is the standard-library behaviour ADR-006 assumes.
  The test pins it.
- `# type: ignore[call-arg]` on `Settings()` in the tests follows the pattern
  handoff 007 left in `tests/unit/delivery/test_config.py`: strict mypy reads
  the synthesised `__init__` as requiring the fields that in fact come from the
  environment.
- `JsonFormatter` timestamps in UTC with `datetime.fromtimestamp(..., tz=UTC)`.
  ADR-006 does not fix a time zone; UTC is the defensible default and is now
  the de facto one for the project.
