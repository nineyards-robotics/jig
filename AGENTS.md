# Jig - Agent Reference

Jig is a declarative ROS 2 node scaffolding framework. You define a node's interface (publishers, subscribers, services, actions, parameters) in a YAML file, and jig generates strongly-typed C++ or Python lifecycle node scaffolding. Nodes use a **session-based composition** pattern (not inheritance) - lifecycle callbacks are free functions that receive a session object containing all ROS entities.

## Supported Distros

Jazzy, Kilted, and Rolling. Humble is **not supported** (Python runtime requires `rclpy.event_handler`, introduced in Iron).

## Installation

Jig must be available in your colcon workspace. Clone it into `src/` alongside your packages:

```bash
cd ~/your_workspace/src
git clone git@github.com:nineyards-robotics/jig.git
```

The jig repo contains two colcon packages (`jig/` and `jig_example/`) inside it — colcon discovers packages recursively, so this just works.

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

## interface.yaml Reference

### Parameters

```yaml
parameters:
  my_param:
    type: string              # Required: bool, int, double, string, none,
                              #   bool_array, int_array, double_array, string_array,
                              #   string_fixed_N, int_array_fixed_N, double_array_fixed_N, string_array_fixed_N
    default_value: "hello"    # Optional: omit to make param required at launch
    description: "A param"    # Optional
    read_only: false          # Optional: if true, only settable at launch (required for QoS param refs)
    validation:               # Optional: generate_parameter_library validators
      bounds: [0, 100]        # Also: lt, gt, lt_eq, gt_eq, one_of, not_empty,
                              #   fixed_size, size_gt, size_lt, unique, subset_of,
                              #   element_bounds, lower_element_bounds, upper_element_bounds
```

### Publishers

```yaml
publishers:
  - topic: some_topic                       # Topic name (required)
    type: std_msgs/msg/String               # ROS message type as package/msg/Type (required)
    qos:                                    # QoS profile (required)
      history: 10                           # Positive int for KEEP_LAST(n), "ALL" for KEEP_ALL, or ${param:name}
      reliability: RELIABLE                 # RELIABLE | BEST_EFFORT | ${param:name}
      durability: VOLATILE                  # Optional: TRANSIENT_LOCAL | VOLATILE | ${param:name}
      deadline_ms: 1000                     # Optional: int or ${param:name}
      liveliness: AUTOMATIC                 # Optional: AUTOMATIC | MANUAL_BY_TOPIC | ${param:name}
      lease_duration_ms: 1000              # Optional: int or ${param:name}
      lifespan_ms: 5000                    # Optional: int or ${param:name}
    field_name: custom_name                 # Optional: override the generated field name (required when topic contains ${param:...})
    manually_created: false                 # Optional: if true, skip code generation (documentation only)
```

### Subscribers

Same fields as publishers.

### Services / Service Clients

```yaml
services:                                   # Or: service_clients
  - name: my_service                        # Service name (required)
    type: example_interfaces/srv/AddTwoInts # ROS service type as package/srv/Type (required)
    field_name: custom_name                 # Optional: override field name
    manually_created: false                 # Optional
```

### Actions / Action Clients

```yaml
actions:                                    # Or: action_clients
  - name: my_action                         # Action name (required)
    type: example_interfaces/action/Fibonacci # ROS action type as package/action/Type (required)
    field_name: custom_name                 # Optional: override field name
    manually_created: false                 # Optional
```

### Parameter Substitution in Names

Use `${param:param_name}` in topic/service/action names to inject parameter values at runtime. When used, you **must** provide `field_name`:

```yaml
publishers:
  - topic: "${param:robot_name}/status"
    field_name: robot_status
    type: std_msgs/msg/String
    qos: { history: 10, reliability: RELIABLE }
```

Use `${for_each_param:array_param_name}` with a `string_array` parameter to generate a map/dict of entities keyed by each parameter value. For example:

```yaml
parameters:
  sensor_names:
    type: string_array
    default_value: ["lidar", "camera"]
    read_only: true

subscribers:
  - topic: "sensor/${for_each_param:sensor_names}/data"
    field_name: sensor_data
    type: sensor_msgs/msg/PointCloud2
    qos: { history: 1, reliability: BEST_EFFORT }
```

This generates `sn->subscribers.sensor_data["lidar"]` and `sn->subscribers.sensor_data["camera"]` (C++) or `sn.subscribers.sensor_data["lidar"]` (Python) - one subscriber per array element.

## C++ Node Pattern

**Header** (`nodes/my_node/my_node.hpp`):
```cpp
#include <my_package/my_node_interface.hpp>  // Auto-generated

namespace my_package::my_node {

struct Session : MyNodeSession<Session> {
    using MyNodeSession::MyNodeSession;  // Required: inherited constructors
    int counter = 0;                     // Custom state goes here
};

CallbackReturn on_configure(std::shared_ptr<Session> sn);

// Must be at pkg::node_name::NodeName - jig expects this exact location
using MyNode = MyNodeBase<Session, on_configure>;

} // namespace my_package::my_node
```

**Implementation** (`nodes/my_node/my_node.cpp`):
```cpp
#include "my_node.hpp"
#include <jig/timer.hpp>
#include <jig/call_sync.hpp>

namespace my_package::my_node {

CallbackReturn on_configure(std::shared_ptr<Session> sn) {
    // Access parameters
    auto val = sn->params.my_param;

    // Publish
    auto msg = std_msgs::msg::String();
    msg.data = "hello";
    sn->publishers.some_topic->publish(msg);

    // Subscribe (callback fires only when ACTIVE)
    sn->subscribers.other_topic->set_callback(
        [](std::shared_ptr<Session> sn, std_msgs::msg::Bool::ConstSharedPtr msg) {
            RCLCPP_INFO(sn->node.get_logger(), "Got: %d", msg->data);
        });

    // Handle service requests
    sn->services.my_service->set_request_handler(
        [](std::shared_ptr<Session> sn, auto request, auto response) {
            response->sum = request->a + request->b;
        });

    // Create timer (starts cancelled, activates with lifecycle)
    jig::create_timer(sn, 1000ms, [](std::shared_ptr<Session> sn) {
        // periodic work
    });

    // Sync service call (safe from on_configure - uses background executor)
    if (sn->service_clients.my_client->wait_for_service(2s)) {
        auto req = std::make_shared<MyService::Request>();
        auto resp = jig::call_sync<MyService>(sn->service_clients.my_client, req, 5s);
    }

    // Action server
    sn->actions.my_action->set_options({.new_goals_replace_current_goal = true});

    return CallbackReturn::SUCCESS;
}

} // namespace my_package::my_node
```

### Additional C++ Lifecycle Callbacks

You can provide more than just `on_configure`. All callbacks are optional free functions with signature `CallbackReturn(std::shared_ptr<Session>)`:

```cpp
CallbackReturn on_configure(std::shared_ptr<Session> sn);
CallbackReturn on_activate(std::shared_ptr<Session> sn);
CallbackReturn on_deactivate(std::shared_ptr<Session> sn);
CallbackReturn on_cleanup(std::shared_ptr<Session> sn);
CallbackReturn on_shutdown(std::shared_ptr<Session> sn);
CallbackReturn on_error(std::shared_ptr<Session> sn);

using MyNode = MyNodeBase<Session, on_configure, on_activate, on_deactivate, on_cleanup, on_shutdown, on_error>;
```

## Python Node Pattern

```python
from dataclasses import dataclass
from my_package.my_node.interface import MyNodeSession, run
from std_msgs.msg import String, Bool
import jig
from jig import TransitionCallbackReturn

@dataclass
class MySession(MyNodeSession):
    counter: int = 0  # Custom state

def on_configure(sn: MySession) -> TransitionCallbackReturn:
    # Access parameters
    val = sn.params.my_param

    # Publish
    sn.publishers.some_topic.publish(String(data="hello"))

    # Subscribe
    def callback(sn: MySession, msg: Bool):
        sn.logger.info(f"Got: {msg.data}")
    sn.subscribers.other_topic.set_callback(callback)

    # Handle service
    def handler(sn: MySession, request, response):
        response.sum = request.a + request.b
        return response
    sn.services.my_service.set_request_handler(handler)

    # Timer (period in seconds)
    jig.create_timer(sn, 1.0, lambda sn: sn.logger.info("tick"))

    # Action server
    sn.actions.my_action.set_options(
        jig.SingleGoalActionServerOptions(new_goals_replace_current_goal=True))

    return TransitionCallbackReturn.SUCCESS

if __name__ == "__main__":
    run(MySession, on_configure)
```

## Session API Cheatsheet

| What | C++ | Python |
|---|---|---|
| Node reference | `sn->node` | `sn.node` |
| Logger | `sn->node.get_logger()` | `sn.logger` |
| Parameters | `sn->params.name` | `sn.params.name` |
| Publish | `sn->publishers.name->publish(msg)` | `sn.publishers.name.publish(msg)` |
| Subscribe callback | `sn->subscribers.name->set_callback(fn)` | `sn.subscribers.name.set_callback(fn)` |
| Service handler | `sn->services.name->set_request_handler(fn)` | `sn.services.name.set_request_handler(fn)` |
| Service client | `sn->service_clients.name` | `sn.service_clients.name` |
| Action get goal | `sn->actions.name->get_active_goal()` | `sn.actions.name.get_active_goal()` |
| Action succeed | `sn->actions.name->succeed(result)` | `sn.actions.name.succeed(result)` |
| Action abort | `sn->actions.name->abort(result)` | `sn.actions.name.abort(result)` |
| Action client | `sn->action_clients.name` | `sn.action_clients.name` |
| Create timer | `jig::create_timer(sn, 1000ms, fn)` | `jig.create_timer(sn, 1.0, fn)` |
| Wall timer | `jig::create_wall_timer(sn, 1000ms, fn)` | `jig.create_wall_timer(sn, 1.0, fn)` |
| Sync service call | `jig::call_sync<SrvT>(client, req, timeout)` | N/A |
| Sync action goal | `jig::send_goal_sync<ActT>(client, goal, opts, timeout)` | N/A |
| Sync action result | `jig::get_result_sync<ActT>(goal_handle, timeout)` | N/A |

Callback signatures:
- **Subscriber:** `(std::shared_ptr<Session>, MsgType::ConstSharedPtr)` / `(sn, msg)`
- **Service handler:** `(std::shared_ptr<Session>, Request::SharedPtr, Response::SharedPtr)` / `(sn, request, response)`
- **Timer:** `(std::shared_ptr<Session>)` / `(sn)`

## Default QoS Handlers

Jig provides built-in QoS event handlers that auto-deactivate the node when a deadline is missed or a publisher is lost. Attach them in `on_configure`:

**C++:**
```cpp
#include <jig/default_qos_handlers.hpp>

// Attach to a specific subscriber or publisher
jig::attach_default_qos_handlers(sn->subscribers.heartbeat, sn);
jig::attach_default_qos_handlers(sn->publishers.some_topic, sn);
```

**Python:**
```python
from jig import attach_default_qos_handlers

attach_default_qos_handlers(sn.subscribers.heartbeat, sn)
attach_default_qos_handlers(sn.publishers.some_topic, sn)
```

This requires the entity to have `deadline_ms` and/or `liveliness`/`lease_duration_ms` set in its QoS config. When a deadline is missed or liveliness changes, the node transitions to INACTIVE.

## Lifecycle Semantics

- **Autostart**: Nodes auto-configure and auto-activate by default (controlled by `autostart` parameter, default `true`)
- **Timers**: Created in cancelled state during `on_configure`, reset/started on activate, cancelled on deactivate
- **Subscribers/Services**: Callbacks only fire when node is in `ACTIVE` state; service requests are rejected when not active
- **Errors are terminal**: Any error state transitions directly to Finalized (no recovery)
- **State heartbeat**: All nodes publish lifecycle state on `~/state` topic with 100ms deadline

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
