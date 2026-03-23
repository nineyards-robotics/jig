#!/bin/bash

# Convenience script to run the jig code generator tests

cd "$(dirname "$0")"

echo "Running jig code generator tests..."
echo ""

pytest -v test_generate_node_interface.py "$@"
