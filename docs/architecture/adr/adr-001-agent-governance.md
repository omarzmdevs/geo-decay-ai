# ADR-001: Agent Governance Model

## Status

Accepted

## Date

2026-10-07

## Context

The project is developed by a single person with AI agents doing most of the
implementation. That raises three problems a conventional setup does not have.

**Vendor lock-in.** The first version of the rules named specific tools and
models throughout, so changing IDE or model family meant rewriting the project's
rules. Tools in this space change faster than the project will.

**Context cost.** Instruction files are loaded on every session. Vendor guidance
targets under 200 lines per instruction file, because longer files both consume
context and reduce adherence. A single file holding every rule for every role
would be paid for in every session and followed in none.

**Unbounded agent authority.** Agents in this project will download orthophotos,
LiDAR tiles and WMS/WFS responses, and will later generate reports with an LLM
over retrieved documents. That is textbook indirect prompt injection exposure:
the agent holds credentials, reads untrusted content and can reach the network.
Instructions alone cannot contain that, because instruction files are context,
not enforced configuration.

## Decision

**Three permanent roles**, each with one owner and one tier:

| Role | Tier | Owns |
|---|---|---|
| Orchestrator | deep / standard | Planning, handoffs, system architecture, ADRs, independent verification |
| Developer | standard (deep for hard GIS/CV) | Code, unit tests, module design within the sprint |
| Documenter | light | Transcribing verified results into project records |

The orchestrator decides *what* and *why*, the developer decides *how*, and the
documenter records *what was verified*. **Tester mode** is not a fourth role but
a flag on the handoff: when acceptance tests are required, a separate developer
session writes them from the criteria before implementation and cannot touch
`src/`; the implementing session cannot touch `tests/acceptance/`.

**Tiers are defined by capability, never by model name.** The mapping from tier
to concrete model lives only in `.agents/TOOLING.md`.

**`AGENTS.md` is the single entry point**, as a real file at the repository root,
read natively by most agent tools. No tool-specific instruction file is
committed, because the presence of one can stop a tool from reading `AGENTS.md`.
Role contracts live in `.agents/roles/` and load on demand, so a session pays
only for the role it takes.

**Three security layers**, because no single one is sufficient:

1. *Instructions* — `AGENTS.md` and the role contracts. Advisory.
2. *Tool permissions and OS sandbox* — deny reads of secrets, deny writes to
   protected paths, deny committing and history rewriting. Enforced by the tool,
   but command-text deny rules are not a boundary around a program, so the
   OS-level sandbox carries the filesystem and network limits.
3. *Write-scope guard* — `scripts/policy_guard.py` validating the working-tree diff
   against `.agents/policy.yaml`, independent of any vendor.

**Agents read git, the user writes it.** Agents may inspect the repository;
staging, committing, reverting, discarding, pushing, branching, merging and
rebasing are the user's actions, and `.git/` is write-denied for agents. Validation happens at two points per task — once per sprint for the
handoffs, once per task for the combined diff — rather than once per role.

## Alternatives Considered

**A single agent for everything.** Simplest and cheapest, and defensible given
that multi-agent systems consume roughly an order of magnitude more tokens than
chat and fit poorly where work has many interdependencies. Rejected because the
agent that writes the code is then the one grading it, and because planning and
transcription have genuinely different capability needs.

**Four permanent roles, with the tester always on.** Rejected: unit tests share
all their context with the code, so a permanent split pays a full extra session
for no independence gain. Tester mode captures the value only where it exists —
acceptance criteria written before the implementation.

**A tool-specific instruction file symlinked to the shared contract.** Works, but
file-writing tools refuse to write through a symlink, a committed symlink
degrades on Windows checkouts, and it reintroduces a vendor filename at the
repository root.

**A `MODELS.md` pinning exact model identifiers.** Rejected in favour of family
aliases: pinned identifiers go stale at every model release, and the mapping is
the one thing guaranteed to change.

## Consequences

**Positive.** Changing tool or vendor touches only `.agents/TOOLING.md` and that
tool's settings directory. Always-loaded context stays small, with role detail
loaded on demand. The limits that matter are enforced by configuration rather
than by instruction, and are verifiable. Work is verified by an agent other than
the one that produced it, in a clean context.

**Negative.** Two validation points per task mean the user is in the loop and
throughput depends on their availability; a governance model that is skipped
under time pressure is worse than a simpler one that is followed. Until
`scripts/policy_guard.py` exists, write scopes rest on review alone. Protected
paths cannot be changed in a headless run, so infrastructure sprints are
necessarily interactive. Role boundaries also add real friction: a developer who
finds a wrong acceptance test must stop and report instead of fixing it.

## Related

- [ADR-002](adr-002-operational-roadmap.md) — operational roadmap
- `AGENTS.md`, `.agents/roles/`, `.agents/policy.yaml`, `.agents/TOOLING.md`
- [Sprint 00 log](../../sprints/sprint-00-agent-setup.md)
