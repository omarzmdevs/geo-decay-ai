# Handoff 009 · CI Quality-Gate Workflow

## Objective

Every push and every pull request to `main` runs the ADR-005 quality gate on
GitHub Actions, using the same hook definition the local commit hook uses.

## Role

developer

## Tier

`TIER_LIGHT` — one workflow file against a gate that is already defined and
already passing. No design latitude.

## Context

Sprint 3, the only handoff of the sprint. The gate exists twice today: as the
commands in `.pre-commit-config.yaml` and as the user's habit of running them.
This handoff adds the third place it must hold — the remote — without writing
the command list a second time: CI runs `pre-commit`, so the gate keeps one
definition.

`.github/workflows/**` is a protected path in `.agents/policy.yaml`. This task
runs only in an interactive session in which the user has lifted the deny entry
for that session.

## Files to Read

- `.pre-commit-config.yaml`
- `pyproject.toml`
- `docs/architecture/adr/adr-005-dependency-and-environment-manager.md`

## Files to Create or Modify

- `.github/workflows/quality-gate.yml` *(protected)*

## Out of Scope

- Any second workflow, and any job that builds or pushes the Docker image.
  ADR-007 reduces this sprint to one workflow running the gate; the image build
  is recorded as deferred in the sprint log.
- Deployment, releases, registry credentials, environments, and anything under
  `secrets.`. The gate needs no secret, so the workflow reads none.
- Changing `.pre-commit-config.yaml`, `pyproject.toml`, `uv.lock` or any source
  or test file. If the gate fails on the current tree, stop and report: that is
  a defect to fix in its own task, not here.
- Branch protection and required status checks, which live in the repository's
  settings on GitHub and are the user's action.
- The status badge in `README.md`, which the orchestrator adds once a run is
  green.

## Execution Mode

**Interactive only**, with the user's explicit approval for the protected path.
Never headless.

## Specification

One file, `.github/workflows/quality-gate.yml`:

- `name: Quality gate`.
- Triggers: `push` with no branch filter, and `pull_request` targeting `main`.
  Work happens on block branches (`bloque-1` today), so a gate that only ran on
  `main` would report nothing during a block.
- `permissions: contents: read` at workflow level. The job reads the code and
  needs nothing else.
- `concurrency` keyed on the workflow and the ref, with
  `cancel-in-progress: true`, so a second push supersedes the run in flight.
- One job, `gate`, on `ubuntu-latest`, with `timeout-minutes` set (15 is ample;
  the gate takes seconds locally).
- Steps:
  1. Check out the repository.
  2. Install uv with the official `astral-sh/setup-uv` action, with its cache
     enabled and keyed on `uv.lock`. The cache directory is repo-local
     (`pyproject.toml` → `[tool.uv] cache-dir = ".uv-cache"`, gitignored); if
     the action cannot cache it, drop the cache rather than moving the
     directory.
  3. `uv sync --frozen` — installs the locked environment and fails if
     `uv.lock` no longer matches `pyproject.toml`.
  4. `uv run pre-commit run --all-files --show-diff-on-failure` — the gate.
- The Python version is **not** named anywhere in the workflow: it comes from
  `.python-version` and `requires-python`, which uv honours. One source of
  truth.
- Every `uses:` is pinned to a release tag (`owner/action@vN`), never to a
  branch and never unpinned.

## Acceptance Tests

no — configuration against a decided gate.

## Acceptance Criteria

1. `.github/workflows/quality-gate.yml` exists and is the only file in
   `.github/workflows/`; it parses as YAML.
2. Triggers: `push` present with no branch filter, and `pull_request` filtered
   to `main`.
3. `permissions.contents` is `read`, and no other permission is granted.
4. `concurrency.cancel-in-progress` is true.
5. Every job sets `timeout-minutes`.
6. Every `uses:` value matches `owner/repo@v<digits>[.digits...]`.
7. The job runs `uv sync --frozen` and
   `uv run pre-commit run --all-files`, in that order.
8. The file contains no `secrets.`, no `docker build` and no `docker push`, and
   names no Python version.
9. `git status --short` shows only the new workflow file.
10. The local gate passes on the tree as delivered.

## Verification Command

```bash
uv run python - <<'PY'
import pathlib, re, sys, yaml

d = pathlib.Path(".github/workflows")
files = sorted(p.name for p in d.iterdir() if p.is_file())
assert files == ["quality-gate.yml"], files
raw = (d / "quality-gate.yml").read_text()
wf = yaml.safe_load(raw)

# PyYAML 1.1 reads the key `on` as the boolean True.
triggers = wf.get("on", wf.get(True))
assert "push" in triggers, triggers
assert not (triggers["push"] or {}).get("branches"), "push must have no branch filter"
assert triggers["pull_request"]["branches"] == ["main"], triggers["pull_request"]

assert wf["permissions"] == {"contents": "read"}, wf["permissions"]
assert wf["concurrency"]["cancel-in-progress"] is True, wf["concurrency"]

steps_run = []
for name, job in wf["jobs"].items():
    assert isinstance(job.get("timeout-minutes"), int), f"{name}: no timeout-minutes"
    for step in job["steps"]:
        if "uses" in step:
            assert re.fullmatch(r"[\w.-]+/[\w.-]+@v\d+(\.\d+)*", step["uses"]), step["uses"]
        if "run" in step:
            steps_run.append(step["run"])

flat = "\n".join(steps_run)
i_sync = flat.find("uv sync --frozen")
i_gate = flat.find("uv run pre-commit run --all-files")
assert i_sync != -1 and i_gate != -1, flat
assert i_sync < i_gate, "uv sync must run before the gate"

for forbidden in ("secrets.", "docker build", "docker push", "python-version"):
    assert forbidden not in raw, forbidden
assert not re.search(r"3\.1[0-9]", raw), "no Python version in the workflow"
print("workflow ok")
PY
uv run pre-commit run --all-files && git status --short
```

A green local run proves the file's shape and that the gate it invokes passes.
It cannot prove GitHub schedules the run: that is the user's follow-up below,
and it is what closes the sprint.

## Launch Command

Interactive session only. First message:
`ROLE: developer. Execute docs/prompts/009-ci-quality-gate-workflow.md`

The user lifts the `.github/**` deny entry for that session and restores it
afterwards.

## Restore Point

`d40898d` — `docs(sprint-03): plan Sprint 3 · CI/CD with handoff 009`, the
commit that froze this sprint's plan. Working tree clean at launch except
`.claude/settings.json`, which carried the user's lift of the deny entry.

## Follow-up for the User

1. Restore the `.github/**` deny entry.
2. Commit, then push the branch and confirm the run is green on GitHub.
3. Optionally require the check on `main` in the repository's branch
   protection.

---

## Run Record

Date: 2026-10-21
Tool and model: in-process developer subagent (`haiku`, matching `TIER_LIGHT`)
launched from the orchestrator's interactive session, with the user's explicit
authorisation for the protected path — the same arrangement recorded for
handoff 004. The user removed the `Edit(./.github/workflows/**)` deny entry
before the launch and restores it afterwards.
Restore point: `d40898d`.
Outcome: completed.

## Verification

Verdict: **ACCEPTED**

Files changed — one, as the handoff lists:

| File | |
|---|---|
| `.github/workflows/quality-gate.yml` | new, the only file under `.github/` |

`.claude/settings.json` also shows as modified: the user's temporary lift of
the deny entry, not part of this task and not to be committed with it. Nothing
else in the tree changed — no source, test, lockfile or hook configuration.

Gate, re-run by the orchestrator: the handoff's verification command prints
`workflow ok`, and `pre-commit run --all-files` passes all six hooks (ruff
check, ruff format --check, strict mypy, import-linter, pytest, policy guard
secrets).

Criteria, checked one by one:

1. `quality-gate.yml` is the only file in `.github/workflows/` and parses as
   YAML. ✔
2. `push` with no branch filter; `pull_request` filtered to `main`. ✔
3. `permissions` is exactly `contents: read`. ✔
4. `concurrency.cancel-in-progress` is true, keyed on workflow and ref. ✔
5. The single job sets `timeout-minutes: 15`. ✔
6. Both `uses:` values are tag-pinned: `actions/checkout@v5`,
   `astral-sh/setup-uv@v7`. ✔
7. `uv sync --frozen` runs before `uv run pre-commit run --all-files`. ✔
8. No `secrets.`, no `docker build`, no `docker push`, no Python version. ✔
9. `git status --short` shows only the new workflow, beside the user's lift. ✔
10. The local gate passes on the tree as delivered. ✔

Notes:

- **The action versions were checked, not taken on trust.** The developer
  reported pinning `actions/checkout@v5` and `astral-sh/setup-uv@v7`; the
  orchestrator fetched each `action.yml` independently (both HTTP 200) and
  confirmed `setup-uv@v7` really exposes `enable-cache`,
  `cache-dependency-glob` and `cache-local-path`. A tag that does not exist is
  the cheapest way to make a first run fail, and nothing local would have
  caught it.
- **The cache is the one unproven element.** `cache-local-path: .uv-cache`
  aligns the action with `[tool.uv] cache-dir` in `pyproject.toml`, but whether
  the cache is actually restored can only be read from a run's log. The
  handoff allows dropping `enable-cache` if it is not; that is a follow-up, not
  a defect.
- **Acceptance is not the same as a working pipeline.** Every criterion here
  describes the file; none can prove GitHub schedules it. The sprint closes on
  the first green run on GitHub, which the sprint log carries as the user's
  task.
- **Debt W3 was not settled by this task.** The question is whether an
  `Edit(...)` deny also stops a write issued from a shell command; the deny
  entry was lifted before the developer ran, so nothing was probed. W3 stands
  unchanged in `next_tasks.md`.

## Sprint Closing Evidence

Date: 2026-10-25
Verdict: the sprint's closing criterion is met.

First green run on GitHub: workflow `Quality gate`, run #2, branch `bloque-1`,
commit `d061937`, conclusion `success` (2026-10-24T23:04:48Z). Read by the
orchestrator from the GitHub Actions API, not from the developer's or the user's
report.

Run #1 (`410f96f`) failed: the SHA pin was malformed — `actions/checkout@v3d3c42e…`
carried a stray `v` before the digest, so the ref did not resolve. Fixed by the
user in `d061937`, which also pins `astral-sh/setup-uv` by digest. That is the
first evidence that the workflow is genuinely scheduled and executed, which no
local check could produce.

Still open as a follow-up, unchanged by this run: whether the uv cache is
actually restored can only be read from a run's log (see the note above), and
debt `CI-PIN` now applies to digests kept in step with their version comments.
