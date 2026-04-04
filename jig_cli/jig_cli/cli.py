"""CLI entry point for jig."""

from __future__ import annotations

import argparse
from glob import glob
import json
import os
import sys

import yaml


def _discover_interfaces() -> list[dict]:
    """Scan AMENT_PREFIX_PATH for installed jig interface YAMLs.

    Returns a deduplicated list of interface dicts. Earlier prefixes win over
    later ones, and native interfaces (directory matches node.package) win over
    vendored copies within the same prefix.
    """
    ament_path = os.environ.get("AMENT_PREFIX_PATH", "")
    if not ament_path:
        return []

    # (package, node_name) -> interface dict
    # Track separately: native hits and vendored hits per prefix ordering
    result: dict[tuple[str, str], dict] = {}

    for prefix in ament_path.split(":"):
        # Collect all interfaces in this prefix, partitioned into native/vendored
        native: dict[tuple[str, str], dict] = {}
        vendored: dict[tuple[str, str], dict] = {}

        for path in glob(os.path.join(prefix, "share", "*", "interfaces", "*.yaml")):
            with open(path) as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict) or "node" not in data:
                continue
            node = data["node"]
            pkg = node.get("package")
            name = node.get("name")
            if not pkg or not name:
                continue

            key = (pkg, name)
            # Directory name is the package that installed this file
            dir_pkg = path.split(os.sep)[-3]  # .../share/<dir_pkg>/interfaces/...
            if dir_pkg == pkg:
                native.setdefault(key, data)
            else:
                vendored.setdefault(key, data)

        # Merge into result: native wins over vendored, earlier prefix wins overall
        for key, data in native.items():
            result.setdefault(key, data)
        for key, data in vendored.items():
            result.setdefault(key, data)

    return list(result.values())


def cmd_interface(args: argparse.Namespace) -> None:
    """Get the interface for a specific package and executable."""
    interfaces = _discover_interfaces()

    for iface in interfaces:
        node = iface["node"]
        if node["package"] != args.package:
            continue
        if args.executable and node["name"] == args.executable:
            match = iface
            break
        if args.plugin and node.get("plugin") == args.plugin:
            match = iface
            break
    else:
        lookup = args.executable or args.plugin
        print(
            f"No interface found for package '{args.package}', "
            f"{'executable' if args.executable else 'plugin'} '{lookup}'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if args.format == "yaml":
        print(yaml.dump(match, default_flow_style=False), end="")
    else:
        print(json.dumps(match))


def cmd_interfaces(args: argparse.Namespace) -> None:
    """List all installed jig node interfaces."""
    interfaces = _discover_interfaces()

    if args.format == "yaml":
        print(yaml.dump(interfaces, default_flow_style=False), end="")
    else:
        print(json.dumps(interfaces))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="jig", description="CLI tools for jig")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # jig interface --package <pkg> (--executable <name> | --plugin <class>)
    interface_parser = subparsers.add_parser(
        "interface", help="Get interface for a specific node"
    )
    interface_parser.add_argument("--package", required=True, help="Package name")
    lookup_group = interface_parser.add_mutually_exclusive_group(required=True)
    lookup_group.add_argument("--executable", help="Executable/node name")
    lookup_group.add_argument("--plugin", help="Component plugin class")
    interface_parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )
    interface_parser.set_defaults(func=cmd_interface)

    # jig interfaces
    interfaces_parser = subparsers.add_parser(
        "interfaces", help="List all installed node interfaces"
    )
    interfaces_parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )
    interfaces_parser.set_defaults(func=cmd_interfaces)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
