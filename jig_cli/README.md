# jig_cli

**CLI tools for discovering and querying jig node interfaces at runtime.**

`jig_cli` provides the `jig` command, which scans your ROS 2 workspace for installed [jig](../README.md) interface definitions and outputs them as JSON or YAML. This is useful for launch systems, developer tooling, and any automation that needs to know what interfaces a node exposes.

## Installation

### pip

```bash
pip install "git+https://github.com/nineyards-robotics/jig.git#subdirectory=jig_cli"
```

### From source

`jig_cli` is a standard ament_python package. Build it alongside the rest of your workspace:

```bash
colcon build --packages-select jig_cli
source install/setup.bash
```

## Usage

### `jig interface` -- look up a single node

Retrieve the interface definition for a specific node by executable name or plugin class:

```bash
# By executable name
jig interface --package my_package --executable my_node

# By C++ component plugin class
jig interface --package my_package --plugin my_package::MyNode

# Output as YAML instead of JSON (default)
jig interface --package my_package --executable my_node --format yaml
```

### `jig interfaces` -- list all installed interfaces

List every jig node interface installed in the current workspace:

```bash
jig interfaces
jig interfaces --format yaml
```

## Discovery

The CLI scans every prefix in `AMENT_PREFIX_PATH` for interface YAML files at the standard install location:

```
<prefix>/share/<package>/interfaces/*.yaml
```

When the same node appears in multiple locations, the following priority rules apply:

1. **Native over vendored** -- an interface installed by its own package wins over a copy installed by another package.
2. **Earlier prefix wins** -- the first match in `AMENT_PREFIX_PATH` order takes precedence.

## Output format

Output defaults to JSON (one line). Use `--format yaml` for human-readable output. Both formats contain the full resolved interface definition including node metadata, parameters, publishers, subscribers, services, actions, and any implicit interfaces.

```json
{
  "node": {
    "name": "my_node",
    "package": "my_package",
    "plugin": "my_package::MyNode"
  },
  "parameters": { ... },
  "publishers": [ ... ],
  "subscribers": [ ... ],
  "services": [ ... ]
}
```
