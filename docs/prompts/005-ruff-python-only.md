# Handoff 005 · Restrict Ruff to Python Files

## Objective

Ruff lints and formats only Python sources, so `ruff format .` can never rewrite
Markdown, including protected paths such as `AGENTS.md`, `.agents/` and
`docs/tfm/`.

## Role

developer

## Tier

`TIER_LIGHT` — a one-key configuration change with a scripted check.

## Files to Read

- `pyproject.toml`

## Files to Create or Modify

- `pyproject.toml`: only the `[tool.ruff]` table

## Out of Scope

- Any other file. Never run `ruff format .` or `ruff check --fix .` without
  `--check`/`--diff` before the change is in place.
- Ruff lint rules, MyPy, Pytest and import-linter configuration.
- `uv.lock`. Dependencies do not change.

## Acceptance Tests

no — configuration.

## Specification

- In `[tool.ruff]`, add `include = ["*.py", "*.pyi", "**/pyproject.toml"]`.
  Ruff 0.16 adds Markdown to its default `include`, and that default is what
  this key replaces.
- Nothing else changes.

## Acceptance Criteria

1. `ruff format --check -v .` includes no `.md` file.
2. `ruff format --check -v .` still includes every Python file under `src/` and
   `tests/`.
3. The full ADR-005 gate passes.
4. `git status --short` shows only `pyproject.toml`.

## Verification Command

```bash
export UV_CACHE_DIR="${UV_CACHE_DIR:-$TMPDIR/uv-cache}"
inc=$(uv run ruff format --check -v . 2>&1 | grep 'Included path via `include`')
! printf '%s\n' "$inc" | grep -q '\.md"' \
  && test "$(printf '%s\n' "$inc" | grep -c '\.py"')" = "$(git ls-files -co --exclude-standard 'src/*.py' 'tests/*.py' | wc -l | tr -d ' ')" \
  && uv run ruff check . && uv run ruff format --check . && uv run mypy \
  && uv run lint-imports && uv run pytest \
  && git status --short
```

## Launch Command

```bash
claude -p --model haiku --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Glob" "Grep" "Bash(uv run *)" \
    "Bash(git status*)" "Bash(git diff*)" \
  "ROLE: developer. Execute docs/prompts/005-ruff-python-only.md" < /dev/null
```

## Restore Point

<!-- Filled by whoever launches: `git rev-parse HEAD` right before launch -->

---

## Run Record

Date: 2026-10-11
Tool and model: Claude Code sub-agent (`haiku`) launched from the orchestrator's
interactive session at the user's request, instead of the headless `claude -p`
command above. The sub-agent inherited the session's permissions, deny rules and
sandbox.
Restore point: 223ada6
Outcome: completed

## Verification

Verdict: ACCEPTED
Files changed: `pyproject.toml` only. Compared with a snapshot taken before
launch, the diff is the single added line
`include = ["*.py", "*.pyi", "**/pyproject.toml"]` in `[tool.ruff]`. `uv.lock`
is unchanged (checksum verified).
Gate: verification command re-run by the orchestrator, exit 0. Ruff now
includes 0 Markdown files, down from 36, and 7 of 7 Python files. Ruff check
and format pass on 7 files, mypy finds no issues, lint-imports reports
`4 kept, 0 broken`, and pytest passes 4 tests.
Notes:
- Launched at the user's request before this handoff was committed, while it
  was staged but not frozen. That deviates from the Task Lifecycle. HEAD was
  clean apart from the staged handoff, so the diff stays attributable.
