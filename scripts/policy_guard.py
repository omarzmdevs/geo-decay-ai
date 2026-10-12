"""Check changed paths against the write-scope policy in ``.agents/policy.yaml``.

Classification uses only the path strings: the guard never opens, reads or stats
a checked path, so a secret is never read and a deleted path is still classified.

Exit codes: 0 no violations, 1 at least one violation, 2 usage or configuration
error.
"""

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SECRET = "SECRET"
PROTECTED = "PROTECTED"
OUT_OF_SCOPE = "OUT_OF_SCOPE"

DEFAULT_POLICY = Path(".agents/policy.yaml")
SUPPORTED_VERSION = 1


class GuardError(Exception):
    """A usage or configuration error (exit code 2)."""


@dataclass(frozen=True)
class Policy:
    secrets_include: tuple[str, ...]
    secrets_except: tuple[str, ...]
    protected: tuple[str, ...]
    roles: dict[str, tuple[str, ...]]


def _string_list(value: Any, where: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise GuardError(f"policy: {where} must be a list of strings")
    return tuple(value)


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise GuardError(f"policy: {where} must be a mapping")
    return value


def load_policy(path: Path) -> Policy:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        raise GuardError(f"cannot read policy {path}: {error}") from error
    except yaml.YAMLError as error:
        raise GuardError(f"cannot parse policy {path}: {error}") from error
    if not isinstance(raw, dict):
        raise GuardError(f"policy {path} is not a mapping")
    if raw.get("version") != SUPPORTED_VERSION:
        raise GuardError(
            f"policy {path}: unsupported version {raw.get('version')!r}, "
            f"expected {SUPPORTED_VERSION}"
        )
    secrets = _mapping(raw.get("secrets"), "secrets")
    roles = {
        str(name): _string_list(_mapping(body, f"roles.{name}").get("write"), name)
        for name, body in _mapping(raw.get("roles"), "roles").items()
    }
    return Policy(
        secrets_include=_string_list(secrets.get("include"), "secrets.include"),
        secrets_except=_string_list(secrets.get("except"), "secrets.except"),
        protected=_string_list(raw.get("protected"), "protected"),
        roles=roles,
    )


def normalize(path: str) -> str:
    while path.startswith("./"):
        path = path[2:]
    return path


def _segment_matches(pattern: str, segment: str) -> bool:
    regex = "".join(
        "[^/]*" if char == "*" else "[^/]" if char == "?" else re.escape(char)
        for char in pattern
    )
    return re.fullmatch(regex, segment) is not None


def _segments_match(pattern: Sequence[str], path: Sequence[str]) -> bool:
    if not pattern:
        return not path
    head, rest = pattern[0], pattern[1:]
    if head == "**":
        return any(_segments_match(rest, path[i:]) for i in range(len(path) + 1))
    return (
        bool(path)
        and _segment_matches(head, path[0])
        and _segments_match(rest, path[1:])
    )


def matches(pattern: str, path: str) -> bool:
    """Gitignore-like match of ``pattern`` against a repo-relative POSIX path."""
    segments = path.split("/")
    if "/" not in pattern:
        return _segment_matches(pattern, segments[-1])
    return _segments_match(pattern.split("/"), segments)


def _matches_any(patterns: Sequence[str], path: str) -> bool:
    return any(matches(pattern, path) for pattern in patterns)


def classify(
    path: str,
    policy: Policy,
    write_globs: Sequence[str] | None,
    allow_protected: bool,
) -> str | None:
    """Return the violation category of ``path``, or ``None`` when it is allowed.

    ``write_globs`` is ``None`` for the secret-only check.
    """
    if _matches_any(policy.secrets_include, path) and not _matches_any(
        policy.secrets_except, path
    ):
        return SECRET
    if write_globs is None:
        return None
    if _matches_any(policy.protected, path):
        return None if allow_protected else PROTECTED
    return None if _matches_any(write_globs, path) else OUT_OF_SCOPE


def parse_porcelain(output: bytes) -> list[str]:
    """Paths from ``git status --porcelain=v1 -z``, both sides of a rename."""
    paths: list[str] = []
    entries = output.decode("utf-8", errors="surrogateescape").split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if entry[0] in "RC" or entry[1] in "RC":
            if index < len(entries) and entries[index]:
                paths.append(entries[index])
            index += 1
    return paths


def changed_paths() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GuardError(f"cannot run git: {error}") from error
    if completed.returncode != 0:
        stderr = completed.stderr.decode(errors="replace").strip()
        raise GuardError(f"git status failed: {stderr}")
    return parse_porcelain(completed.stdout)


def check(
    paths: Sequence[str],
    policy: Policy,
    roles: Sequence[str] | None,
    allow_protected: bool,
) -> list[tuple[str, str]]:
    """Return ``(category, path)`` violations sorted by path."""
    write_globs: list[str] | None = None
    if roles is not None:
        write_globs = []
        for role in roles:
            if role not in policy.roles:
                raise GuardError(f"unknown role: {role}")
            write_globs.extend(policy.roles[role])
    violations: dict[str, str] = {}
    for raw_path in paths:
        path = normalize(raw_path)
        category = classify(path, policy, write_globs, allow_protected)
        if category is not None:
            violations[path] = category
    return [(category, path) for path, category in sorted(violations.items())]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check changed paths against the write-scope policy."
    )
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--role", action="append", dest="roles")
    mode.add_argument("--secrets-only", action="store_true")
    parser.add_argument("--allow-protected", action="store_true")
    parser.add_argument("paths", nargs="*", metavar="PATH")
    return parser


def run(argv: Sequence[str]) -> int:
    args = build_parser().parse_args(argv)
    policy = load_policy(args.policy)
    roles: list[str] | None = None if args.secrets_only else args.roles
    paths = args.paths if args.paths else changed_paths()
    violations = check(paths, policy, roles, args.allow_protected)
    for category, path in violations:
        sys.stdout.write(f"{category}\t{path}\n")
    return 1 if violations else 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except GuardError as error:
        sys.stderr.write(f"policy_guard: {error}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
