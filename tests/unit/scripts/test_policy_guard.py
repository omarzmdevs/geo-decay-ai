"""Unit tests of the internal functions of ``scripts/policy_guard.py``."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "policy_guard.py"


def load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("policy_guard", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


guard = load_guard()


@pytest.mark.parametrize(
    ("pattern", "path", "expected"),
    [
        (".env", ".env", True),
        (".env", "config/.env", True),
        (".env.*", "sub/.env.prod", True),
        ("*.txt", "a/b/c.txt", True),
        ("src/*.py", "src/a.py", True),
        ("src/*.py", "src/x/a.py", False),
        ("src/*.py", "other/src/a.py", False),
        ("**/*.pem", "a.pem", True),
        ("**/*.pem", "x/y/a.pem", True),
        (".agents/**", ".agents/roles/developer.md", True),
        ("lib/**/*.py", "lib/a.py", True),
        ("lib/**/*.py", "lib/x/y/a.py", True),
        ("lib/**/*.py", "x/lib/a.py", False),
        ("file?.cfg", "file1.cfg", True),
        ("file?.cfg", "file10.cfg", False),
        ("file?.cfg", "file.cfg", False),
        ("a.b", "axb", False),
    ],
)
def test_matches(pattern: str, path: str, expected: bool) -> None:
    assert guard.matches(pattern, path) is expected


def test_normalize_strips_leading_dot_slash() -> None:
    assert guard.normalize("./a/b") == "a/b"
    assert guard.normalize("a/./b") == "a/./b"


def test_parse_porcelain_returns_both_sides_of_a_rename() -> None:
    output = b" M a.py\0R  new.py\0old.py\0?? with space.md\0 D gone.py\0"
    assert guard.parse_porcelain(output) == [
        "a.py",
        "new.py",
        "old.py",
        "with space.md",
        "gone.py",
    ]


def test_parse_porcelain_empty() -> None:
    assert guard.parse_porcelain(b"") == []


def make_policy() -> object:
    return guard.Policy(
        secrets_include=(".env", ".env.*"),
        secrets_except=(".env.example",),
        protected=("AGENTS.md",),
        roles={"dev": ("src/**",)},
    )


@pytest.mark.parametrize(
    ("path", "allow_protected", "expected"),
    [
        (".env", False, "SECRET"),
        (".env", True, "SECRET"),
        (".env.example", False, "OUT_OF_SCOPE"),
        ("AGENTS.md", False, "PROTECTED"),
        ("AGENTS.md", True, None),
        ("README.md", False, "OUT_OF_SCOPE"),
        ("src/a.py", False, None),
    ],
)
def test_classify(path: str, allow_protected: bool, expected: str | None) -> None:
    result = guard.classify(path, make_policy(), ("src/**",), allow_protected)
    assert result == expected


def test_classify_without_write_globs_checks_secrets_only() -> None:
    assert guard.classify("README.md", make_policy(), None, False) is None
    assert guard.classify("AGENTS.md", make_policy(), None, False) is None
    assert guard.classify(".env", make_policy(), None, False) == "SECRET"


def test_check_sorts_and_deduplicates() -> None:
    result = guard.check(["b.py", "./b.py", ".env"], make_policy(), ["dev"], False)
    assert result == [("SECRET", ".env"), ("OUT_OF_SCOPE", "b.py")]


def test_check_unknown_role_raises() -> None:
    with pytest.raises(guard.GuardError):
        guard.check(["a.py"], make_policy(), ["nobody"], False)


def test_load_policy_rejects_wrong_version(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("version: 2\n")
    with pytest.raises(guard.GuardError):
        guard.load_policy(policy)


def test_load_policy_rejects_malformed_globs(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("version: 1\nprotected: not-a-list\n")
    with pytest.raises(guard.GuardError):
        guard.load_policy(policy)


def test_load_policy_missing_file(tmp_path: Path) -> None:
    with pytest.raises(guard.GuardError):
        guard.load_policy(tmp_path / "missing.yaml")


def test_load_policy_reads_roles(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("version: 1\nroles:\n  dev:\n    write: ['src/**']\n")
    loaded = guard.load_policy(policy)
    assert loaded.roles == {"dev": ("src/**",)}
    assert loaded.protected == ()
