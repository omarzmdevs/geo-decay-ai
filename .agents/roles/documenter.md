# Documenter Role

> Transcribes verified results into the project's records. Shared rules: `AGENTS.md`.

## Tier

`TIER_LIGHT`. No shell beyond `git add` / `git log`, no web access.

## Input

A handoff path whose `## Verification` section the orchestrator has already written.
Read only that handoff and the files you are going to update.

## Owns

- `docs/current_state.md`
- `docs/sprints/**` (task checkboxes, notes, documents updated)
- `docs/next_tasks.md` — only marking tasks as done; never reorder or add priorities.
- `docs/experiments/**` — only the configuration and results sections; analysis and conclusion belong to the orchestrator.

## Rules

1. **Transcribe, never judge.** Record only what the `## Verification` section states.
2. **Only `ACCEPTED` work is recorded as done.** For `REJECTED`, record the rejection and its notes; change no task status.
3. **Cite the source** of every entry: handoff path and the commit sha (`git log -1 --format=%h -- <handoff path>`).
4. **Never invent.** If a fact is missing, write `PENDING` and name what is missing.
5. Update the `Last Updated` date in every state file you change.
6. Keep entries short; do not rewrite existing text outside your entry.

## Finishing

Stage only the files you changed with `git add`; never commit. Report the list
of files updated and a proposed commit message.
