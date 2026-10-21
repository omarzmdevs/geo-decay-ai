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

<!-- Filled by whoever launches: `git rev-parse HEAD` right before launch -->

## Follow-up for the User

1. Restore the `.github/**` deny entry.
2. Commit, then push the branch and confirm the run is green on GitHub.
3. Optionally require the check on `main` in the repository's branch
   protection.

---

## Run Record

<!-- Filled by whoever launches the task -->

Date:
Tool and model:
Outcome: <!-- completed | failed | aborted -->

## Verification

<!-- Filled by the orchestrator, after re-running the verification command itself -->

Verdict: <!-- ACCEPTED | REJECTED -->
Files changed:
Gate:
Notes:
