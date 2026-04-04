"""Session-scoped fixtures for jig_cli tests.

Builds the test workspace once per session so that interface YAML files
are installed and discoverable via AMENT_PREFIX_PATH.

The jig package source is copied into the test workspace at build time
so tests always build against the current jig source without requiring
the outer workspace to be built first.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

from jig_cli.cli import main
import pytest

TEST_WS = Path(__file__).parent / "test_ws"
JIG_PKG_SRC = Path(__file__).parents[2] / "jig"


def _build_test_ws() -> Path:
    """Build the test workspace if needed. Returns the install directory."""
    install_dir = TEST_WS / "install"
    jig_dest = TEST_WS / "src" / "jig"

    # Always sync jig source into test_ws
    if jig_dest.exists():
        shutil.rmtree(jig_dest)
    shutil.copytree(JIG_PKG_SRC, jig_dest)

    src_mtime = max(
        f.stat().st_mtime for f in (TEST_WS / "src").rglob("*") if f.is_file()
    )
    needs_build = not install_dir.exists() or install_dir.stat().st_mtime < src_mtime

    if needs_build:
        subprocess.check_call(
            ["colcon", "build"],
            cwd=str(TEST_WS),
        )

    return install_dir


@pytest.fixture(scope="session")
def test_ws_install() -> Path:
    """Build test workspace and return install directory path."""
    return _build_test_ws()


@pytest.fixture(scope="session")
def test_ws_env(test_ws_install) -> dict[str, str]:
    """Return an environment dict with the test workspace on AMENT_PREFIX_PATH."""
    setup_bash = test_ws_install / "setup.bash"
    assert setup_bash.exists(), f"setup.bash not found at {setup_bash}"

    result = subprocess.run(
        ["bash", "-c", f"source {setup_bash} && env -0"],
        capture_output=True,
        text=True,
        check=True,
    )

    env = {}
    for entry in result.stdout.split("\0"):
        if "=" in entry:
            key, _, value = entry.partition("=")
            env[key] = value

    return env


@pytest.fixture
def run_jig(test_ws_env, monkeypatch, capsys):
    """Return a function that calls jig CLI main() directly.

    Sets AMENT_PREFIX_PATH so the CLI can discover installed interfaces.
    """

    def _run(*argv: str) -> tuple[int, str, str]:
        """Run jig CLI with the given args. Returns (exit_code, stdout, stderr)."""
        monkeypatch.setenv("AMENT_PREFIX_PATH", test_ws_env["AMENT_PREFIX_PATH"])
        try:
            main(list(argv))
            code = 0
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return _run
