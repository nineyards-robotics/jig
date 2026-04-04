"""CLI entry point for jig."""

from __future__ import annotations

import argparse
import json


def cmd_interface(args: argparse.Namespace) -> None:
    """Get the interface for a specific package and executable."""
    print(json.dumps({}))


def cmd_interfaces(args: argparse.Namespace) -> None:
    """List all installed jig node interfaces."""
    print(json.dumps([]))


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
