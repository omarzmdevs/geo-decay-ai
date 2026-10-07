# Handoff NNN · Title

## Objective

<!-- One outcome-oriented sentence -->

## Role

<!-- developer | developer (tester mode) | documenter -->

## Tier

<!-- TIER_LIGHT | TIER_STANDARD | TIER_DEEP, plus a one-line justification -->

## Files to Read

<!-- Explicit and minimal: every file listed is context the role pays for -->

## Files to Create or Modify

<!-- Explicit. Must fall inside the role's scope in .agents/policy.yaml -->

## Out of Scope

<!-- What must not be touched -->

## Acceptance Tests

<!-- yes | no. 'yes' only for critical logic: abandonment index, georeferencing,
     detection, data contracts -->

## Acceptance Criteria

<!-- Checks a script can run, not prose -->

## Verification Command

<!-- The exact command that proves the criteria -->

## Launch Command

<!-- From .agents/TOOLING.md, with the allowlist narrowed to this task -->

## Restore Point

<!-- Output of `git rev-parse HEAD` before the task starts -->

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
