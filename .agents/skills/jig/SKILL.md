---
name: jig
description: Declarative ROS 2 node scaffolding framework. Use when creating, modifying, or working with jig-based ROS 2 packages, interface.yaml files, or jig lifecycle nodes in C++ or Python. Covers package setup, interface definitions, session API, and build configuration.
license: Apache-2.0
compatibility: Requires ROS 2 Jazzy, Kilted, or Rolling. Requires colcon build system.
metadata:
  author: nineyards-robotics
  repository: https://github.com/nineyards-robotics/jig
---

# Jig

Jig is a declarative ROS 2 node scaffolding framework. You define a node's interface (publishers, subscribers, services, actions, parameters) in a YAML file, and jig generates strongly-typed C++ or Python lifecycle node scaffolding. Nodes use a **session-based composition** pattern (not inheritance) - lifecycle callbacks are free functions that receive a session object containing all ROS entities.

## Supported Distros

Jazzy, Kilted, and Rolling. Humble is **not supported** (Python runtime requires `rclpy.event_handler`, introduced in Iron).

## Installation

Jig must be available in your colcon workspace. Clone it into `src/` alongside your packages:

```bash
cd ~/your_workspace/src
git clone git@github.com:nineyards-robotics/jig.git
```

The jig repo contains two colcon packages (`jig/` and `jig_example/`) inside it - colcon discovers packages recursively, so this just works.

Then build the workspace as usual:

```bash
cd ~/your_workspace
colcon build
```

Jig packages (`jig`, plus any packages you create) will be discovered and built automatically by colcon. Your packages just need `<depend>jig</depend>` in `package.xml` and `find_package(jig REQUIRED)` in `CMakeLists.txt`.

## Package Structure

```
my_package/
├── nodes/
│   ├── my_node/                # One directory per node
│   │   ├── interface.yaml      # Required: declares the node's ROS interface
│   │   ├── my_node.hpp         # C++ header (or .py for Python)
│   │   └── my_node.cpp         # C++ implementation
│   └── another_node/           # Multiple nodes per package supported
│       ├── interface.yaml
│       └── another_node.py
├── interfaces/                 # Optional: custom msg/srv/action definitions
│   ├── msg/
│   ├── srv/
│   └── action/
├── launch/                     # Optional: auto-installed if present
├── config/                     # Optional: auto-installed if present
├── CMakeLists.txt
└── package.xml
```

**Minimal CMakeLists.txt:**
```cmake
cmake_minimum_required(VERSION 3.22)
project(my_package)

find_package(jig REQUIRED)
jig_auto_package()
```

For interface-only packages (no nodes, just msg/srv/action definitions), use `jig_auto_interface_package()` instead.

**Note:** Jig always uses `ament_cmake` as the build type, even for Python-only nodes. You do **not** need `setup.py`, `setup.cfg`, or `ament_python`. Jig's CMake macros handle Python installation internally.

**Minimal package.xml:**
```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>my_package</name>
  <version>0.0.0</version>
  <description>My jig package</description>
  <maintainer email="you@example.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <depend>jig</depend>

  <!-- Add for C++ nodes -->
  <depend>rclcpp</depend>

  <!-- Add for Python nodes -->
  <depend>rclpy</depend>

  <!-- Add message/service/action packages your interface.yaml references -->
  <depend>std_msgs</depend>
  <depend>example_interfaces</depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

The `<depend>` entries must include `jig` plus every ROS package referenced by your `type:` fields in interface.yaml (e.g., `std_msgs` for `std_msgs/msg/String`).

## Constraints

- **No mixed languages**: Each node directory must be purely C++ or purely Python, not both
- **Node name != package name**: The node directory name cannot match the CMake project name (namespace collision)
- **Single-threaded executor**: Main node uses single-threaded executor. Service client responses use an isolated background executor to prevent deadlock during sync calls
- **Naming**: Node names are `snake_case`. Generated C++ classes are `PascalCase`. Namespace is `package_name::node_name`
- **Generated include path**: C++ nodes include `<package_name/node_name_interface.hpp>`. Python imports from `package_name.node_name.interface`

## Common Pitfalls

- **Missing inherited constructors (C++)**: You must write `using MyNodeSession::MyNodeSession;` in your Session struct. Without it, the code compiles but crashes at runtime because the base session is never properly constructed.
- **Wrong namespace (C++)**: Jig expects the node type at exactly `package_name::node_name::NodeName` (PascalCase). If the namespace is wrong, the component registration silently fails and the node won't be found at runtime.
- **Setup outside on_configure**: All callbacks, timers, and entity setup must happen inside `on_configure` (or later lifecycle callbacks). Don't set up subscribers or timers in the Session constructor.
- **Using `${param:...}` without `field_name`**: When a topic/service/action name contains a parameter reference, you must provide an explicit `field_name` since the generated field name can't be derived from a dynamic string.
- **Node name matches package name**: If your node directory is named the same as the CMake project, you get a namespace collision. Rename one of them.

## Detailed Reference

See [references/REFERENCE.md](references/REFERENCE.md) for the complete interface.yaml spec, C++ and Python node patterns, session API cheatsheet, QoS handlers, and lifecycle semantics.
