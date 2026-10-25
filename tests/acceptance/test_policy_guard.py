"""Acceptance tests for ``scripts/policy_guard.py`` (handoff 003).

Written from the handoff's Specification only. The guard is run as a subprocess
with explicit paths, a temporary policy file, or a throwaway git repository.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD = REPO_ROOT / "scripts" / "policy_guard.py"
REAL_POLICY = REPO_ROOT / ".agents" / "policy.yaml"

Result = subprocess.CompletedProcess[str]


def run_guard(args: list[str], cwd: Path = REPO_ROOT, timeout: float = 60) -> Result:
    # A missing script makes Python itself exit 2, which would satisfy the
    # usage-error cases vacuously.
    assert GUARD.is_file(), f"{GUARD} does not exist"
    return subprocess.run(
        [sys.executable, str(GUARD), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def parse_violations(result: Result) -> dict[str, str]:
    """Map each reported path to its category, asserting the line format."""
    violations: dict[str, str] = {}
    for line in result.stdout.splitlines():
        category, sep, path = line.partition("\t")
        assert sep == "\t", f"line is not '<CATEGORY>\\t<path>': {line!r}"
        violations[path] = category
    return violations


def write(root: Path, relative: str, content: str = "x\n") -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


# --- Table from the handoff, against the real policy ---------------------------

TABLE: list[tuple[list[str], list[str], int, list[str]]] = [
    (["--role", "developer"], ["src/geo_decay_domain/x.py"], 0, []),
    (["--role", "developer"], [".env"], 1, ["SECRET\t.env"]),
    (["--role", "developer"], ["sub/.env.prod"], 1, ["SECRET\tsub/.env.prod"]),
    (["--role", "developer"], [".env.local"], 1, ["SECRET\t.env.local"]),
    (["--role", "developer"], [".env.example"], 0, []),
    (["--role", "developer"], ["keys/a.pem"], 1, ["SECRET\tkeys/a.pem"]),
    (["--role", "developer"], ["AGENTS.md"], 1, ["PROTECTED\tAGENTS.md"]),
    (
        ["--role", "developer"],
        [".claude/settings.json"],
        1,
        ["PROTECTED\t.claude/settings.json"],
    ),
    (["--role", "developer", "--allow-protected"], ["Dockerfile"], 0, []),
    (["--role", "developer", "--allow-protected"], [".env"], 1, ["SECRET\t.env"]),
    (["--role", "documenter"], ["src/a.py"], 1, ["OUT_OF_SCOPE\tsrc/a.py"]),
    (
        ["--role", "documenter", "--role", "developer"],
        ["src/a.py", "docs/current_state.md"],
        0,
        [],
    ),
    (["--role", "orchestrator"], ["docs/prompts/001-x.md"], 0, []),
    (
        ["--role", "tester"],
        ["tests/unit/test_a.py"],
        1,
        ["OUT_OF_SCOPE\ttests/unit/test_a.py"],
    ),
    (["--role", "tester"], ["tests/acceptance/test_a.py"], 0, []),
    (["--secrets-only"], ["AGENTS.md", "src/a.py"], 0, []),
    (["--secrets-only"], ["credentials.json"], 1, ["SECRET\tcredentials.json"]),
    (
        ["--role", "developer"],
        ["b.py", ".env", "a.pem"],
        1,
        ["SECRET\t.env", "SECRET\ta.pem", "OUT_OF_SCOPE\tb.py"],
    ),
]


@pytest.mark.parametrize(
    ("args", "paths", "exit_code", "expected"),
    TABLE,
    ids=[" ".join(args + paths) for args, paths, _, _ in TABLE],
)
def test_handoff_table(
    args: list[str], paths: list[str], exit_code: int, expected: list[str]
) -> None:
    result = run_guard([*args, *paths])
    assert result.returncode == exit_code, result.stderr
    assert result.stdout.splitlines() == expected


@pytest.mark.parametrize(
    "args",
    [
        ["--role", "nobody"],
        ["--role", "developer", "--role", "nobody"],
        [],
        ["--allow-protected"],
        ["--role", "developer", "--policy", "missing.yaml"],
    ],
    ids=["unknown-role", "one-unknown-role", "no-flag", "only-allow", "missing-policy"],
)
def test_usage_and_configuration_errors_exit_2(args: list[str]) -> None:
    result = run_guard([*args, "src/a.py"])
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() != ""


def test_leading_dot_slash_is_stripped_before_matching() -> None:
    clean = run_guard(["--role", "developer", "./src/a.py"])
    assert clean.returncode == 0
    assert clean.stdout == ""

    secret = run_guard(["--role", "developer", "./.env"])
    assert secret.returncode == 1
    assert secret.stdout.startswith("SECRET\t")


def test_secret_wins_over_protected_and_out_of_scope() -> None:
    # `.git/hooks/x.pem` is a secret and protected; only SECRET is reported.
    result = run_guard(["--role", "documenter", ".git/hooks/x.pem"])
    assert result.stdout.splitlines() == ["SECRET\t.git/hooks/x.pem"]


def test_protected_wins_over_out_of_scope() -> None:
    # AGENTS.md is protected and in nobody's scope; only PROTECTED is reported.
    result = run_guard(["--role", "documenter", "AGENTS.md"])
    assert result.stdout.splitlines() == ["PROTECTED\tAGENTS.md"]


def test_guard_never_opens_checked_paths(tmp_path: Path) -> None:
    # A FIFO named `.env` blocks forever if the guard tries to open it.
    os.mkfifo(tmp_path / ".env")
    write(tmp_path, "keys/a.pem", "TOP-SECRET-CANARY\n")
    result = run_guard(
        ["--policy", str(REAL_POLICY), "--role", "developer", ".env", "keys/a.pem"],
        cwd=tmp_path,
        timeout=30,
    )
    assert result.returncode == 1
    assert parse_violations(result) == {".env": "SECRET", "keys/a.pem": "SECRET"}
    assert "TOP-SECRET-CANARY" not in result.stdout + result.stderr


# --- Path matching, against a temporary policy ---------------------------------

MATCHING_POLICY = """\
version: 1
secrets:
  include:
    - "*.secret"
    - "vault/*.key"
    - "**/*.pem"
  except:
    - "public.secret"
protected:
  - "frozen/**"
roles:
  dev:
    write:
      - "docs/*.md"
      - "*.txt"
      - "lib/**/*.py"
      - "file?.cfg"
"""

MATCHING_CASES: dict[str, str | None] = {
    # Pattern without `/`: final component at any depth.
    "a.secret": "SECRET",
    "x/y/a.secret": "SECRET",
    "a.txt": None,
    "x/y/a.txt": None,
    # `secrets.except` removes a path from the secret set, at any depth.
    "public.secret": "OUT_OF_SCOPE",
    "x/public.secret": "OUT_OF_SCOPE",
    # Pattern with `/`: anchored at the root, and `*` does not cross `/`.
    "vault/a.key": "SECRET",
    "x/vault/a.key": "OUT_OF_SCOPE",
    "vault/sub/a.key": "OUT_OF_SCOPE",
    "docs/a.md": None,
    "x/docs/a.md": "OUT_OF_SCOPE",
    "docs/sub/a.md": "OUT_OF_SCOPE",
    # `**` as a whole segment matches zero or more segments.
    "a.pem": "SECRET",
    "x/y/a.pem": "SECRET",
    "lib/a.py": None,
    "lib/x/y/a.py": None,
    "other/a.py": "OUT_OF_SCOPE",
    "x/lib/a.py": "OUT_OF_SCOPE",
    "frozen/a.bin": "PROTECTED",
    "frozen/x/y/a.bin": "PROTECTED",
    "x/frozen/a.bin": "OUT_OF_SCOPE",
    # `?` matches exactly one character.
    "file1.cfg": None,
    "file10.cfg": "OUT_OF_SCOPE",
    "file.cfg": "OUT_OF_SCOPE",
    # Leading `./` is stripped.
    "./docs/b.md": None,
}


def test_path_matching_rules(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text(MATCHING_POLICY)
    result = run_guard(
        ["--policy", str(policy), "--role", "dev", *MATCHING_CASES], cwd=tmp_path
    )
    expected = {
        path: category
        for path, category in MATCHING_CASES.items()
        if category is not None
    }
    assert result.returncode == 1, result.stderr
    assert parse_violations(result) == expected


def test_violations_are_sorted_by_path(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text(MATCHING_POLICY)
    result = run_guard(
        ["--policy", str(policy), "--role", "dev", "z.secret", "m/a.py", "a.pem"],
        cwd=tmp_path,
    )
    paths = [line.split("\t", 1)[1] for line in result.stdout.splitlines()]
    assert paths == ["a.pem", "m/a.py", "z.secret"]


def test_roles_are_unioned(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        "version: 1\nsecrets: {include: [], except: []}\nprotected: []\n"
        "roles:\n  r1: {write: ['a/**']}\n  r2: {write: ['b/**']}\n"
    )
    base = ["--policy", str(policy)]
    both = run_guard([*base, "--role", "r1", "--role", "r2", "a/x", "b/x"], tmp_path)
    assert both.returncode == 0
    assert both.stdout == ""
    one = run_guard([*base, "--role", "r1", "a/x", "b/x"], tmp_path)
    assert one.returncode == 1
    assert one.stdout.splitlines() == ["OUT_OF_SCOPE\tb/x"]


@pytest.mark.parametrize(
    "content",
    [
        MATCHING_POLICY.replace("version: 1", "version: 2"),
        MATCHING_POLICY.replace("version: 1\n", ""),
        "version: [unclosed\n  - : :\n",
        "",
    ],
    ids=["version-2", "no-version", "unparsable", "empty"],
)
def test_bad_policy_exits_2(tmp_path: Path, content: str) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text(content)
    result = run_guard(["--policy", str(policy), "--role", "dev", "a.txt"], tmp_path)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() != ""


# --- Working-tree mode, against a throwaway git repository ---------------------


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.com",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A clean repository with the real policy at the default location."""
    git(tmp_path, "init", "-q")
    (tmp_path / ".agents").mkdir()
    shutil.copy(REAL_POLICY, tmp_path / ".agents" / "policy.yaml")
    write(tmp_path, "README.md", "readme\n")
    write(tmp_path, "src/keep.py", "keep\n")
    write(tmp_path, "src/old.py", "content of the old module\n")
    write(tmp_path, "docs/gone.md", "this one will be deleted\n")
    write(tmp_path, "docs/old.md", "content of the old document\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "initial")
    return tmp_path


def make_dirty(repo: Path) -> dict[str, str]:
    """Touch the working tree; return the expected violations for `developer`."""
    (repo / "README.md").write_text("changed\n")  # modified, out of scope
    (repo / "src/keep.py").write_text("changed\n")  # modified, in scope
    (repo / "docs/gone.md").unlink()  # deleted
    git(repo, "mv", "src/old.py", "docs/new.md")  # rename: new path is out
    git(repo, "mv", "docs/old.md", "src/new.py")  # rename: old path is out
    write(repo, "newdir/sub/x.txt")  # untracked, listed file by file
    write(repo, "docs/with space.md")  # needs NUL-separated parsing
    write(repo, ".env", "SECRET=1\n")  # untracked secret
    return {
        ".env": "SECRET",
        "README.md": "OUT_OF_SCOPE",
        "docs/gone.md": "OUT_OF_SCOPE",
        "docs/new.md": "OUT_OF_SCOPE",
        "docs/old.md": "OUT_OF_SCOPE",
        "docs/with space.md": "OUT_OF_SCOPE",
        "newdir/sub/x.txt": "OUT_OF_SCOPE",
    }


def test_clean_working_tree_passes(repo: Path) -> None:
    result = run_guard(["--role", "developer"], repo)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_working_tree_changes_are_all_checked(repo: Path) -> None:
    expected = make_dirty(repo)
    result = run_guard(["--role", "developer"], repo)
    assert result.returncode == 1, result.stderr
    assert result.stdout.splitlines() == [
        f"{category}\t{path}" for path, category in sorted(expected.items())
    ]


def test_working_tree_secrets_only(repo: Path) -> None:
    make_dirty(repo)
    result = run_guard(["--secrets-only"], repo)
    assert result.returncode == 1, result.stderr
    assert result.stdout.splitlines() == ["SECRET\t.env"]


def test_explicit_paths_replace_the_working_tree_scan(repo: Path) -> None:
    make_dirty(repo)
    result = run_guard(["--role", "developer", "src/keep.py"], repo)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
