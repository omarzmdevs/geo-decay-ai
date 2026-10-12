# Tooling

> The **only** file that names concrete tools and models. Everything else refers
> to roles and tiers. To add or replace a tool, edit this file and that tool's
> own settings directory.

## Requirements for Any Agent Tool

A tool may fill a role in this repository only if it is configured so that:

1. It reads `AGENTS.md` (natively or through a user-level setting outside the repository) — no instruction file of its own is committed.
2. It denies reading secrets (`.agents/policy.yaml` → `secrets`), with `.env.example` as the only exception.
3. It denies writing protected paths (`.agents/policy.yaml` → `protected`).
4. Shell commands run sandboxed — writes confined to the repository, network limited to an allowlist — or each command is reviewed by the user.
5. Commands that launch other agents require the user's approval; never auto-approve them.
6. It never runs with a mode that disables permissions.
7. No tool-server configuration (e.g. MCP) is committed to the repository.
8. It cannot write to git: agents leave changes in the working tree, and the user stages, commits and pushes. Reading (`status`, `diff`, `log`) is allowed; the index and `.git/` are denied.

Configuration that lives outside the repository (user-level settings) is the
user's responsibility; record here only what the repository needs.

## Tier → Model

Use family aliases, not pinned versions, so the mapping survives model releases.

| Tier | Use for | Alias (Claude Code) |
|---|---|---|
| `TIER_LIGHT` | Transcription, boilerplate, configuration, simple scripts | `haiku` |
| `TIER_STANDARD` | Most code and tests, routine handoffs, verification | `sonnet` |
| `TIER_DEEP` | Sprint planning, architecture, ADRs, hard GIS/CV/ML work | `opus` |

Other tools: map each tier to the model family with equivalent capability.

## Launch Commands (Claude Code)

Claude Code reads `AGENTS.md` natively from v2.1.277 when no `CLAUDE.md`
exists. Copy the matching command into the handoff's **Launch command** field
and adjust the allowlist to the task. `dontAsk` denies every tool not
pre-approved; dry-run a new command on a trivial handoff before relying on it.

The prompt goes right after `-p`, before any flag. `--allowedTools` takes a
variable number of values, so a prompt placed after it is parsed as one more
tool name and the run aborts with "Input must be provided".

**Developer:**

```bash
claude -p "ROLE: developer. Execute docs/prompts/NNN-short-title.md" \
  --model sonnet --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv run *)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

Every gate tool runs through `uv run`, so it uses the version locked in `uv.lock`
(ADR-005). Add `"Bash(uv sync*)"` and `"Bash(uv lock*)"` only when the handoff
changes dependencies.

**Tester mode:** same command with
`"ROLE: developer, tester mode. Execute the acceptance-test part of docs/prompts/NNN-short-title.md"`.

**Documenter:**

```bash
claude -p "ROLE: documenter. Record the verification of docs/prompts/NNN-short-title.md" \
  --model haiku --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" < /dev/null
```

Interactive sessions start with the first message `ROLE: <role>`.
Tasks touching protected paths run only in an interactive session.

## Claude Code Settings — `.claude/settings.json`

Enforces requirements 2–4 and part of 6.

- Only the "nobody touches" list is enforced there. Role scopes are checked by the working-tree guard, because a deny rule in shared settings would block every role.
- `.git/**` is denied for writing, which is what keeps requirement 8 true rather than merely stated. The OS-level sandbox enforces it even for shell commands.
- Deny rules cannot carve exceptions, so `.env` variants are listed one by one to keep `.env.example` readable. Add any new `.env.<name>` file to the list.
- Bash deny rules match command text only; the sandbox is the OS-level boundary.
- The sandbox network allowlist (`sandbox.network.allowedDomains`) holds only what uv needs: `pypi.org` and `files.pythonhosted.org` for packages; `github.com`, `objects.githubusercontent.com` and `release-assets.githubusercontent.com` for the Python builds uv downloads. Data domains (IGN/CNIG) are added by the sprint that downloads data.
- Infrastructure sprints need the matching deny entries lifted for that session, with the user's approval.

## Pending Verification

- `dontAsk` behaviour in headless runs (dry-run before first real use).
- Sandbox compatibility with Docker and package installation during Sprint 1.
- uv cache inside the sandbox: a sandboxed session may be denied uv's default
  cache directory. Workaround observed in handoff 003 (tester mode, 2026-10-12):
  `uv run --offline --cache-dir "$TMPDIR/uv-cache" …`, which leaves the
  repository untouched. A permanent fix (e.g. `UV_CACHE_DIR` in the tool
  settings) is the user's decision.
