"""Shared test utilities for jig_example launch tests."""

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from lifecycle_msgs.msg import State, Transition

from lifecycle_msgs.srv import ChangeState, GetState

TIMEOUT = 10.0


def wait_for_node_state(node: Node, name: str, target_state: int, timeout: float = TIMEOUT) -> bool:
    """Wait until a lifecycle node reaches the target state by polling ~/get_state."""
    client = node.create_client(GetState, f"{name}/get_state")
    if not client.wait_for_service(timeout_sec=timeout):
        node.destroy_client(client)
        return False

    end_time = node.get_clock().now() + rclpy.duration.Duration(seconds=timeout)
    while node.get_clock().now() < end_time:
        future = client.call_async(GetState.Request())
        rclpy.spin_until_future_complete(node, future, timeout_sec=2.0)
        if future.result() is not None and future.result().current_state.id == target_state:
            node.destroy_client(client)
            return True
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_client(client)
    return False


def transition_node(node: Node, name: str, transition_id: int, timeout: float = TIMEOUT) -> bool:
    """Call ~/change_state to drive a lifecycle transition. Returns True on success."""
    client = node.create_client(ChangeState, f"{name}/change_state")
    if not client.wait_for_service(timeout_sec=timeout):
        node.destroy_client(client)
        return False

    request = ChangeState.Request()
    request.transition = Transition(id=transition_id)
    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    result = future.result()
    node.destroy_client(client)
    return result is not None and result.success


def wait_for_topic_message(node: Node, topic: str, msg_type, timeout: float = TIMEOUT, qos=10, predicate=None):
    """Subscribe to a topic and return the first message matching predicate (or first message)."""
    result = [None]

    def callback(msg):
        if result[0] is None and (predicate is None or predicate(msg)):
            result[0] = msg

    sub = node.create_subscription(msg_type, topic, callback, qos)
    end_time = node.get_clock().now() + rclpy.duration.Duration(seconds=timeout)
    while result[0] is None and node.get_clock().now() < end_time:
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_subscription(sub)
    return result[0]


def collect_topic_messages(node: Node, topic: str, msg_type, duration: float, qos=10):
    """Collect all messages on a topic for the given duration."""
    messages = []

    def callback(msg):
        messages.append(msg)

    sub = node.create_subscription(msg_type, topic, callback, qos)
    end_time = node.get_clock().now() + rclpy.duration.Duration(seconds=duration)
    while node.get_clock().now() < end_time:
        rclpy.spin_once(node, timeout_sec=0.05)

    node.destroy_subscription(sub)
    return messages


def call_service(node: Node, name: str, srv_type, request, timeout: float = TIMEOUT):
    """Create a temporary service client, call the service, return the response."""
    client = node.create_client(srv_type, name)
    if not client.wait_for_service(timeout_sec=timeout):
        node.destroy_client(client)
        return None

    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    result = future.result()
    node.destroy_client(client)
    return result


def send_action_goal(node: Node, name: str, action_type, goal, timeout: float = TIMEOUT):
    """Create a temporary action client, send goal, return the goal handle."""
    from rclpy.action import ActionClient

    action_client = ActionClient(node, action_type, name)
    if not action_client.wait_for_server(timeout_sec=timeout):
        action_client.destroy()
        return None

    future = action_client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    goal_handle = future.result()
    # Don't destroy client yet - caller needs it for result
    return goal_handle, action_client


def send_action_goal_with_feedback(node: Node, name: str, action_type, goal, timeout: float = TIMEOUT):
    """Send a goal and collect feedback. Returns (goal_handle, action_client, feedback_list)."""
    from rclpy.action import ActionClient

    feedback_list = []
    action_client = ActionClient(node, action_type, name)
    if not action_client.wait_for_server(timeout_sec=timeout):
        action_client.destroy()
        return None, None, []

    future = action_client.send_goal_async(
        goal,
        feedback_callback=lambda fb: feedback_list.append(fb.feedback),
    )
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    goal_handle = future.result()
    return goal_handle, action_client, feedback_list


def get_action_result(node: Node, goal_handle, timeout: float = TIMEOUT):
    """Wait for an action result from an accepted goal handle."""
    future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    return future.result()


def publish_message(node: Node, topic: str, msg_type, msg, qos=10):
    """Create a temporary publisher, publish a message, then destroy it."""
    pub = node.create_publisher(msg_type, topic, qos)
    # Brief spin to allow discovery
    rclpy.spin_once(node, timeout_sec=0.1)
    pub.publish(msg)
    rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_publisher(pub)


def state_qos():
    """QoS profile matching the lifecycle ~/state publisher (transient local)."""
    return QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=1,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
    )
