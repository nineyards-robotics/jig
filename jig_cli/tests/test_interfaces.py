"""Tests for `jig interfaces` command."""

from __future__ import annotations

import json

import yaml


def test_returns_all_interfaces(run_jig):
    """jig interfaces returns all 3 interfaces from both packages."""
    code, stdout, _ = run_jig("interfaces")
    assert code == 0
    result = json.loads(stdout)
    assert isinstance(result, list)
    assert len(result) == 3


def test_format_yaml(run_jig):
    """jig interfaces --format yaml outputs valid YAML."""
    code, stdout, _ = run_jig("interfaces", "--format", "yaml")
    assert code == 0
    result = yaml.safe_load(stdout)
    assert isinstance(result, list)
    assert len(result) == 3


def test_empty_when_no_ament_prefix_path(monkeypatch, capsys):
    """jig interfaces returns empty list when AMENT_PREFIX_PATH is unset."""
    from jig_cli.cli import main

    monkeypatch.delenv("AMENT_PREFIX_PATH", raising=False)
    main(["interfaces"])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result == []
