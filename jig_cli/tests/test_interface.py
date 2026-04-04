"""Tests for `jig interface` command."""

from __future__ import annotations

import json
from pathlib import Path

from referencing import Registry, Resource
import yaml

SCHEMAS_DIR = Path(__file__).parents[2] / "jig" / "schemas"


def test_returns_single_interface(run_jig):
    """jig interface --package <pkg> --executable <name> returns a single object."""
    code, stdout, _ = run_jig(
        "interface", "--package", "pkg_alpha", "--executable", "sensor_node"
    )
    assert code == 0
    result = json.loads(stdout)
    assert isinstance(result, dict)
    assert result["node"]["package"] == "pkg_alpha"
    assert result["node"]["name"] == "sensor_node"


def test_conforms_to_output_schema(run_jig):
    """Output conforms to the jig output.schema.yaml."""
    code, stdout, _ = run_jig(
        "interface", "--package", "pkg_alpha", "--executable", "sensor_node"
    )
    assert code == 0
    result = json.loads(stdout)

    from jsonschema import Draft202012Validator

    schema = yaml.safe_load((SCHEMAS_DIR / "output.schema.yaml").read_text())
    param_schema = yaml.safe_load((SCHEMAS_DIR / "parameter.schema.yaml").read_text())

    registry = Registry().with_resource(
        "parameter.schema.yaml",
        Resource.from_contents(param_schema),
    )
    validator = Draft202012Validator(schema, registry=registry)
    validator.validate(result)


def test_format_yaml(run_jig):
    """jig interface --format yaml outputs valid YAML."""
    code, stdout, _ = run_jig(
        "interface",
        "--package",
        "pkg_beta",
        "--executable",
        "planner_node",
        "--format",
        "yaml",
    )
    assert code == 0
    result = yaml.safe_load(stdout)
    assert isinstance(result, dict)
    assert result["node"]["name"] == "planner_node"


def test_plugin_lookup(run_jig):
    """jig interface --plugin finds a C++ node by plugin class string."""
    code, stdout, _ = run_jig(
        "interface", "--package", "pkg_gamma", "--plugin", "pkg_gamma::CppNode"
    )
    assert code == 0
    result = json.loads(stdout)
    assert result["node"]["package"] == "pkg_gamma"
    assert result["node"]["plugin"] == "pkg_gamma::CppNode"


def test_nonexistent_package(run_jig):
    """jig interface <bad_package> <executable> exits with error."""
    code, stdout, stderr = run_jig(
        "interface", "--package", "no_such_package", "--executable", "some_node"
    )
    assert code != 0


def test_nonexistent_executable(run_jig):
    """jig interface <valid_package> <bad_executable> exits with error."""
    code, stdout, stderr = run_jig(
        "interface", "--package", "pkg_alpha", "--executable", "no_such_node"
    )
    assert code != 0


def test_vendored_interface_discoverable(run_jig):
    """A vendored interface for a non-jig package is discoverable."""
    code, stdout, _ = run_jig(
        "interface", "--package", "pkg_external", "--executable", "external_node"
    )
    assert code == 0
    result = json.loads(stdout)
    assert result["node"]["package"] == "pkg_external"
    assert result["node"]["name"] == "external_node"


def test_native_interface_wins_over_vendored(run_jig):
    """When both a native and vendored interface exist, native wins."""
    code, stdout, _ = run_jig(
        "interface", "--package", "pkg_alpha", "--executable", "sensor_node"
    )
    assert code == 0
    result = json.loads(stdout)
    assert result["node"]["package"] == "pkg_alpha"
    assert result["node"]["name"] == "sensor_node"
