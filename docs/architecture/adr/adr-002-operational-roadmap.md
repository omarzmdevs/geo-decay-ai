# ADR-002: Operational Roadmap and Block 1 Composition

## Status

Accepted

## Date

2026-10-07

## Context

The block and sprint plan lived only in `docs/tfm/TFM_v1.md`: the thesis
document, written in Spanish and listed as a protected path. Agents could not use
it as an operational reference, both because the documentation convention is
English and because nothing may be changed there without the user.

The consequence surfaced in a project review. `docs/next_tasks.md` had drifted
into a numbering that does not exist in the plan — it listed MLOps as Sprint 2
of Block 1 and code quality as Sprint 3, when the plan puts code quality in
Block 1 and MLOps in Block 2 as Sprints 4–6. The backlog in the same file still
cited Sprints 8, 11 and 14 correctly, which showed the plan itself was intact and
only the operational list had diverged. Nothing detected it because no file held
the authoritative structure in a form agents were allowed to read and maintain.

A second problem was structural. `AGENTS.md` requires the quality gate to pass
before any work is reported finished, but the plan delivered Ruff, Black, MyPy, Pytest and
pre-commit in Sprint 2, after Sprint 1 had already produced the project skeleton.
The write-scope guard had no slot at all. The contract therefore demanded a gate
that would not exist for the first sprint, and the project would have had to be
restructured once it arrived.

## Decision

**`docs/roadmap.md` is the operational source of truth for the plan.** It holds
the three phases, the eight blocks and the twenty-six sprints in English, each
with its objective and deliverable. Every agent reads it to know what exists.
`docs/next_tasks.md` keeps only the active slice and links to it.

`docs/tfm/TFM_v1.md` remains the thesis narrative and reference material, but no
longer governs execution. Where the two differ, the roadmap governs and the
deviation is recorded in an ADR.

**Block 1 is recomposed**, keeping twenty-six sprints and the existing numbering:

| Sprint | Before | Now |
|---|---|---|
| 1 | Initialisation | Foundations and Quality Gate — structure, environment, containers, **plus** the full quality gate and the write-scope guard |
| 2 | Code quality | Runtime Foundations — logging, environment variables, centralised configuration |
| 3 | CI/CD | CI/CD, unchanged |

Blocks 2 to 8 are unchanged.

## Alternatives Considered

**Keep `TFM_v1.md` as the source and translate on demand.** Rejected: it is
protected and in Spanish, so every agent reading the plan would either breach the
documentation convention or need the user to relay it, which is what produced the
drift in the first place.

**Merge Sprint 2 into Sprint 1 and renumber to twenty-five sprints.** Rejected:
it would invalidate the backlog's references to Sprints 8, 11 and 14 and break
the numbering correspondence with the thesis document for no benefit. Splitting
the old Sprint 2 along the line that matters — structural tooling versus runtime
concerns — achieves the same goal without renumbering.

**Relax the contract so the gate applies from Sprint 2.** Honest but weak: it
would leave the first sprint without automated quality control and normalise
exceptions to the rules in the first week of development.

## Consequences

**Positive.** One file defines the plan, in the language and location agents can
maintain, so the same drift cannot recur silently. The quality gate and the guard
exist before any business logic, which makes the contract's quality rule true
from the first change and avoids a structural refactor later. Numbering
and backlog references survive untouched.

**Negative.** Sprint 1 grows considerably and is entirely interactive, since
nearly all of its deliverables are protected paths. The roadmap now duplicates
information held in the thesis document, so the two can diverge; the authority
note and this record are what make that divergence a decision rather than an
error. The thesis memoria must explain the deviation from the original plan.

## Related

- [ADR-001](adr-001-agent-governance.md) — agent governance model
- [Roadmap](../../roadmap.md), [Next Tasks](../../next_tasks.md)
- [Sprint 01 log](../../sprints/sprint-01-foundations.md)
