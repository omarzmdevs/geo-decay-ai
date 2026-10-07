# Sprint 00 · Documentation and Agent Setup

> Logged retroactively on 2026-10-07. This sprint had been marked complete in
> `current_state.md` without a log, and the agent governance work that followed
> was not recorded anywhere.

## Block

Block 0 · Project setup (precedes Block 1 of [roadmap.md](../roadmap.md))

## Goal

Establish the repository, the documentation structure and the governance model
for AI-assisted development, before any code is written.

## Requirements

* Git repository with secrets excluded and `.env.example` as the key reference.
* Documentation structure under `docs/`, usable as an Obsidian vault.
* Templates for ADRs, experiments and sprint logs.
* A vendor-neutral agent contract with defined roles and write scopes.
* An operational, English projection of the thesis plan.

## Tasks

- [x] Create the repository, `.gitignore` and `.env.example`.
- [x] Create the `docs/` structure and its templates.
- [x] Write the shared agent contract in `AGENTS.md` as the single entry point,
      with no tool-specific instruction file.
- [x] Define three roles in `.agents/roles/` — orchestrator, developer (with
      tester mode) and documenter — with tiers by capability.
- [x] Define write scopes, secrets and protected paths in `.agents/policy.yaml`.
- [x] Isolate every vendor, model and launch command in `.agents/TOOLING.md`.
- [x] Enforce the non-negotiable limits in the tool's own permission settings:
      deny reads of secrets, deny writes to protected paths, deny committing and
      history rewriting, enable the OS-level sandbox.
- [x] Record the governance decision in ADR-001 and the operational plan in
      ADR-002.
- [x] Create `docs/roadmap.md` as the operational source of truth and align
      `current_state.md` and `next_tasks.md` with it.

## Deliverable

A documented, versioned repository whose AI-assisted development model is
explicit, vendor-neutral and partly enforced by tooling.

## Handoffs Executed

None. This sprint bootstrapped the handoff cycle itself, so it ran in
interactive sessions with the user's explicit approval.

## Notes

- A project review found that `next_tasks.md` had drifted from the thesis plan,
  inventing a sprint numbering in which MLOps belonged to Block 1. Resolved by
  making `roadmap.md` the operational source of truth (ADR-002).
- The quality gate and the write-scope guard were moved into Sprint 1 so that no
  business logic is written before they exist.
- Write scopes are documented but not yet enforced; the guard is a Sprint 1
  deliverable.

## Documents Updated

- [docs/current_state.md](../current_state.md)
- [docs/next_tasks.md](../next_tasks.md)
- [docs/roadmap.md](../roadmap.md)
- [docs/architecture/architecture.md](../architecture/architecture.md)
- ADR-001, ADR-002

## Date Started

2026-09-04

## Date Completed

2026-10-07
