"""Tests for general CLI behavior."""

from __future__ import annotations

from jig_cli.cli import main


def test_no_subcommand_exits_with_error(capsys):
    """jig with no subcommand exits with non-zero code."""
    try:
        main([])
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert e.code != 0


def test_interface_missing_args_exits_with_error(capsys):
    """jig interface with no args exits with error."""
    try:
        main(["interface"])
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert e.code != 0


def test_interface_requires_executable_or_plugin(capsys):
    """jig interface --package alone exits with error."""
    try:
        main(["interface", "--package", "pkg_alpha"])
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert e.code != 0


def test_interface_executable_and_plugin_mutually_exclusive(capsys):
    """jig interface with both --executable and --plugin exits with error."""
    try:
        main(
            [
                "interface",
                "--package",
                "pkg_alpha",
                "--executable",
                "sensor_node",
                "--plugin",
                "pkg_alpha::SensorNode",
            ]
        )
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert e.code != 0
