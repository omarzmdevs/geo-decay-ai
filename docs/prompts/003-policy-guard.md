# Handoff 003 · Write-Scope Policy Guard

## Objective

`scripts/policy_guard.py` checks a set of changed paths against
`.agents/policy.yaml` and fails on any secret, protected path, or path outside
the given roles' write scopes. Role boundaries are then enforced, not just
documented (finding E1, W2).

## Role

developer — tester mode first, then implementation in a separate session.

## Tier

`TIER_STANDARD` — a self-contained CLI with precise path-matching rules.

## Files to Read

- `.agents/policy.yaml`
- `pyproject.toml`
- This handoff's Specification. The tester reads nothing else.

## Files to Create or Modify

**Tester mode:**
- `tests/acceptance/test_policy_guard.py`

**Implementation:**
- `scripts/policy_guard.py`
- `tests/unit/scripts/test_policy_guard.py` (unit tests of internal functions)
- `pyproject.toml`: add `pyyaml` and `types-PyYAML` to the `dev` group, and
  `"scripts"` to MyPy `files`
- `uv.lock`

## Out of Scope

- `.agents/policy.yaml`. If the guard needs a policy change, stop and report it.
- `.pre-commit-config.yaml` (handoff 004).
- Tool settings directories (`.claude/`, ...).
- Implementation must not edit `tests/acceptance/`.

## Acceptance Tests

**yes.** Recommended by the orchestrator because of the guard's role in the
architecture, not because of any ambiguity. The role contract reserves `yes`
for domain logic, so this is a deliberate exception: the guard is the only
automatic enforcement of the write scopes, and its tests should not be written
by the same session that writes the guard.

## Specification

**Interface**

```
python scripts/policy_guard.py [--policy PATH]
    (--role ROLE [--role ROLE ...] | --secrets-only)
    [--allow-protected]
    [PATH ...]
```

- `--policy` defaults to `.agents/policy.yaml`, relative to the current directory.
- If one or more `PATH` arguments are given, exactly those paths are checked.
  Without them, the guard checks every changed path in the working tree
  (`git status --porcelain=v1 -z --untracked-files=all`): modified, added,
  deleted and untracked paths, and both the old and the new path of a rename.
- Several `--role` flags check against the union of those roles' `write` globs.
- `--secrets-only` runs only the secret check, and is what the commit hook uses.
- `--allow-protected` accepts protected paths. It is only for interactive tasks
  where the user has authorised protected changes. It never relaxes the secret
  check.

**Path matching** (gitignore-like, applied to repository-relative POSIX paths;
a leading `./` is stripped):

- A pattern containing `/` is anchored at the repository root. A pattern
  without `/` matches the final path component at any depth (`.env` matches
  `.env` and `config/.env`).
- `*` matches any run of characters except `/`. `?` matches one character
  except `/`. `**` as a whole segment matches zero or more segments
  (`**/*.pem` matches `a.pem` and `x/y/a.pem`; `.agents/**` matches
  `.agents/roles/developer.md`).
- `secrets.except` removes a path from the secret set (`.env.example` is not a
  secret, while `.env.local` and `sub/.env.prod` are).

**Classification**, one category per path, applied in this order:

1. `SECRET`: matches `secrets.include` and no `secrets.except`.
2. `PROTECTED`: matches `protected`, unless `--allow-protected` is given.
3. `OUT_OF_SCOPE`: with `--role`, the path matches no `write` glob of the given
   roles. A protected path accepted by `--allow-protected` is allowed.

**Output and exit codes**

- Each violation prints one line to stdout, `<CATEGORY>\t<path>`, sorted by path.
- Exit `0`: no violations, including when there is nothing to check.
- Exit `1`: at least one violation.
- Exit `2`: usage or configuration error. That covers an unknown role, a
  missing or unparsable policy file, a policy `version` other than `1`, or
  neither `--role` nor `--secrets-only`. The message goes to stderr.
- The guard never opens, reads or stats the checked paths. Classification uses
  only the path strings, so a secret is never read and a deleted path is still
  classified.

**Cases the acceptance tests must cover**, at minimum. The tests run the
script as a subprocess with `sys.executable` and pass explicit paths, plus a
temporary policy file where needed:

| Args | Paths | Exit | Output contains |
|---|---|---|---|
| `--role developer` | `src/geo_decay_domain/x.py` | 0 | — |
| `--role developer` | `.env` | 1 | `SECRET\t.env` |
| `--role developer` | `sub/.env.prod` | 1 | `SECRET\tsub/.env.prod` |
| `--role developer` | `.env.example` | 0 | — |
| `--role developer` | `keys/a.pem` | 1 | `SECRET\tkeys/a.pem` |
| `--role developer` | `AGENTS.md` | 1 | `PROTECTED\tAGENTS.md` |
| `--role developer --allow-protected` | `Dockerfile` | 0 | — |
| `--role developer --allow-protected` | `.env` | 1 | `SECRET\t.env` |
| `--role documenter` | `src/a.py` | 1 | `OUT_OF_SCOPE\tsrc/a.py` |
| `--role documenter --role developer` | `src/a.py`, `docs/current_state.md` | 0 | — |
| `--role orchestrator` | `docs/prompts/001-x.md` | 0 | — |
| `--role tester` | `tests/unit/test_a.py` | 1 | `OUT_OF_SCOPE\ttests/unit/test_a.py` |
| `--secrets-only` | `AGENTS.md`, `src/a.py` | 0 | — |
| `--secrets-only` | `credentials.json` | 1 | `SECRET\tcredentials.json` |
| `--role nobody` | `src/a.py` | 2 | — |
| *(no role flag)* | `src/a.py` | 2 | — |
| `--role developer --policy missing.yaml` | `src/a.py` | 2 | — |
| `--role developer` | `b.py`, `.env`, `a.pem` | 1 | lines sorted by path |

## Acceptance Criteria

1. Tester commit: `uv run pytest tests/acceptance/test_policy_guard.py` fails
   before `scripts/policy_guard.py` exists.
2. After implementation, `tests/acceptance/` is identical to the tester commit
   (`git diff --quiet HEAD -- tests/acceptance`).
3. The acceptance and unit tests pass.
4. Run against the real policy, `.env` is reported as `SECRET`, `AGENTS.md` as
   `PROTECTED`, and `src/a.py` under `--role documenter` as `OUT_OF_SCOPE`.
5. The implementation's own working-tree diff passes
   `policy_guard.py --role developer`.
6. The full ADR-005 gate passes, with MyPy covering `scripts/`.

## Verification Command

```bash
guard() { want=$1; line=$2; shift 2
  out=$(uv run python scripts/policy_guard.py "$@"); rc=$?
  [ "$rc" = "$want" ] && printf '%s\n' "$out" | grep -qxF "$(printf "$line")" \
    || { echo "FAIL ($rc): $*"; return 1; }; }
git diff --quiet HEAD -- tests/acceptance \
  && uv sync --locked \
  && uv run ruff check . && uv run ruff format --check . && uv run mypy \
  && uv run lint-imports && uv run pytest \
  && guard 1 'SECRET\t.env' --role developer .env \
  && guard 1 'PROTECTED\tAGENTS.md' --role developer AGENTS.md \
  && guard 1 'OUT_OF_SCOPE\tsrc/a.py' --role documenter src/a.py \
  && uv run python scripts/policy_guard.py --role developer \
  && git status --short
```

## Launch Command

Tester mode, headless:

```bash
claude -p "ROLE: developer, tester mode. Execute the acceptance-test part of docs/prompts/003-policy-guard.md" \
  --model sonnet --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" "Bash(uv run *)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

Implementation, headless, after the user commits the failing tests:

```bash
claude -p "ROLE: developer. Execute docs/prompts/003-policy-guard.md" \
  --model sonnet --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv lock*)" "Bash(uv sync*)" "Bash(uv run *)" "Bash(mkdir *)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

## Restore Point

<!-- Filled by whoever launches: `git rev-parse HEAD` right before launch -->

Tester mode: 80522d2

## Follow-ups for the User (protected paths)

Once this handoff is accepted:
- Add `scripts/policy_guard.py` to the tool write-deny list (`.claude/settings.json`)
  so no agent can modify its own guard.
- Consider listing it under `protected` in `.agents/policy.yaml`.

---

## Run Record

Date: 2026-10-12
Tool and model: Claude Code headless, `claude -p --model sonnet` (tester mode, then
implementation), launched from an interactive orchestrator session with
`UV_CACHE_DIR="$TMPDIR/uv-cache"`. The prompt was moved before `--allowedTools`
(see `.agents/TOOLING.md`). The nested sessions could not start their own
sandbox and ran their allowlisted commands unsandboxed.
Outcome: completed

## Verification

Verdict: ACCEPTED (experimental run; criteria 1, 2 and 5 not verifiable)
Files changed: `scripts/policy_guard.py`, `tests/unit/scripts/test_policy_guard.py`,
`pyproject.toml`, `uv.lock`; tester: `tests/acceptance/test_policy_guard.py`.
Gate: `uv sync --locked`, ruff check, ruff format --check, mypy (10 files, incl.
`scripts/`), lint-imports (4 kept) and pytest (76 passed, 38 acceptance) all pass;
the three guard checks against the real policy report `SECRET`, `PROTECTED` and
`OUT_OF_SCOPE` as required.
Notes:
- The user authorised an experimental run on a dirty tree with the acceptance
  tests uncommitted. Criterion 1 (red commit) does not exist; the tests were seen
  failing (38/38) before implementation, but not committed. Criterion 2 was
  replaced by a SHA-256 check of the test file, unchanged by the implementation.
  Criterion 5: `--role developer` on the tree flags only the files outside the
  developer scope (`.agents/TOOLING.md`, `.claude/settings.json`, this handoff,
  the acceptance test); every implementation path is in scope.
- Deviation: `explicit_package_bases = true` added to `[tool.mypy]`, required
  because the unit and acceptance test modules share a basename.
- `--role` with `--secrets-only` is rejected by argparse (exit 2); the spec left it open.
- Follow-ups for the user: protect `scripts/policy_guard.py` (tool deny list,
  optionally `protected` in `.agents/policy.yaml`); a permanent uv cache fix for
  sandboxed sessions.
