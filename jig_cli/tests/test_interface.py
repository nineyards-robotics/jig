"""Tests for `jig interface` command."""

from __future__ import annotations

import json
from pathlib import Path

from referencing import Registry, Resource
import yaml

SCHEMAS_DIR = Path(__file__).parents[2] / "jig" / "schemas"


def test_returns_single_interface(run_jig):
    """jig interface <package> <executable> returns a single object."""
    code, stdout, _ = run_jig("interface", "pkg_alpha", "sensor_node")
    assert code == 0
    result = json.loads(stdout)
    assert isinstance(result, dict)
    assert result["node"]["package"] == "pkg_alpha"
    assert result["node"]["name"] == "sensor_node"


def test_conforms_to_output_schema(run_jig):
    """Output conforms to the jig output.schema.yaml."""
    code, stdout, _ = run_jig("interface", "pkg_alpha", "sensor_node")
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
    """jig interface <package> <executable> --format yaml outputs valid YAML."""
    code, stdout, _ = run_jig("interface", "pkg_beta", "planner_node")
    assert code == 0
    result = yaml.safe_load(stdout)
    assert isinstance(result, dict)
    assert result["node"]["name"] == "planner_node"


def test_nonexistent_package(run_jig):
    """jig interface <bad_package> <executable> exits with error."""
    code, stdout, stderr = run_jig("interface", "no_such_package", "some_node")
    assert code != 0


def test_nonexistent_executable(run_jig):
    """jig interface <valid_package> <bad_executable> exits with error."""
    code, stdout, stderr = run_jig("interface", "pkg_alpha", "no_such_node")
    assert code != 0
