# Handoff 004 · Pre-commit Quality Gate

## Objective

Every commit the user makes runs the full ADR-005 quality gate, plus the
secret check of the policy guard, through local hooks that use the locked tool
versions.

## Role

developer

## Tier

`TIER_LIGHT` — one configuration file with a pattern fixed by ADR-005.

## Files to Read

- `docs/architecture/adr/adr-005-dependency-and-environment-manager.md`
- `pyproject.toml`
- `docs/prompts/003-policy-guard.md` → Specification → Interface

## Files to Create or Modify

- `.pre-commit-config.yaml` *(protected)*

## Out of Scope

- Remote hook repositories. ADR-005 requires `repo: local` only.
- `pyproject.toml`, `scripts/`, `tests/`.
- Installing the hook into `.git/hooks`. The user runs `uv run pre-commit install`,
  because `.git/` is off limits to agents.

## Acceptance Tests

no — configuration.

## Execution Mode

**Interactive only**, with the user's explicit approval: `.pre-commit-config.yaml`
is protected.

## Specification

- A single `repo: local` block, with `language: system` and entries run through
  `uv run`. There is one hook per gate step:
  `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, `pytest`, plus
  `policy-guard-secrets` running `uv run python scripts/policy_guard.py --secrets-only`.
- `mypy`, `lint-imports` and `pytest` analyse the whole project, not the staged
  files: `pass_filenames: false`, `always_run: true`. The same applies to
  `ruff check .` and `ruff format --check .`, so the hook and the gate command
  behave identically.
- `policy-guard-secrets` receives the staged filenames (`pass_filenames: true`,
  `always_run: true`) so that a secret staged by mistake blocks the commit.
  It does not check role scopes: the user's commit legitimately combines
  several roles and authorised protected changes. Role checks are run by the
  orchestrator during verification with `--role`.

## Acceptance Criteria

1. Every hook in `.pre-commit-config.yaml` is `repo: local`, and every `entry`
   starts with `uv run`.
2. The six hooks listed above exist.
3. `uv run pre-commit run --all-files` passes on the current tree.
4. `uv run pre-commit validate-config` passes.
5. `git status --short` shows only `.pre-commit-config.yaml`.

## Verification Command

```bash
uv run pre-commit validate-config \
  && test "$(grep -E '^\s*-?\s*repo:' .pre-commit-config.yaml | grep -cv 'repo: local')" = 0 \
  && test "$(grep -E '^\s*entry:' .pre-commit-config.yaml | grep -cv 'entry: uv run')" = 0 \
  && for h in ruff-check ruff-format mypy lint-imports pytest policy-guard-secrets; do \
       grep -Eq "id: $h\$" .pre-commit-config.yaml || { echo "missing $h"; exit 1; }; done \
  && uv run pre-commit run --all-files \
  && git status --short
```

Hook ids must be exactly the six names above.

## Launch Command

Interactive session only. First message:
`ROLE: developer. Execute docs/prompts/004-pre-commit-gate.md`

## Restore Point

<!-- Filled by whoever launches: `git rev-parse HEAD` right before launch -->

0c9b8a7

## Follow-up for the User

After acceptance and commit: `uv run pre-commit install`.

---

## Run Record

Date: 2026-10-12
Tool and model: Claude Code, in-process developer subagent (`haiku`, matching
`TIER_LIGHT`) launched from the interactive orchestrator session, with the user's
authorisation for the protected file and the deny entry lifted for the session.
Outcome: completed

## Verification

Verdict: ACCEPTED
Files changed: `.pre-commit-config.yaml` (new). `.claude/settings.json` also shows
as modified: the user's temporary lift of the deny entry, not part of this task.
Gate: `pre-commit validate-config` passes; one `repo: local` block, every entry
starts with `uv run`; the six hook ids are present; `pre-commit run --all-files`
passes all six hooks (ruff check, ruff format --check, mypy, import-linter,
pytest, policy guard secrets).
Notes:
- Run with `UV_CACHE_DIR="$TMPDIR/uv-cache"` and `--offline` because of the sandbox
  (see `.agents/TOOLING.md` → Pending Verification).
- Launched as a subagent of the orchestrator session, not as a separate
  interactive session; verification was run independently by the orchestrator.
- Follow-ups for the user: restore the `Edit(./.pre-commit-config.yaml)` deny
  entry, commit, then run `uv run pre-commit install`.
