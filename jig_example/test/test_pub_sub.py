"""Tests for publisher/subscriber functionality."""

import unittest

from helpers import TIMEOUT, collect_topic_messages, transition_node, wait_for_node_state
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from lifecycle_msgs.msg import State, Transition
from std_msgs.msg import String


@pytest.mark.launch_test
def generate_test_description():
    return launch.LaunchDescription(
        [
            launch_ros.actions.Node(
                package="jig_example",
                executable="echo_node",
                name="echo_node",
                namespace="echo_node",
                output="screen",
            ),
            launch_ros.actions.Node(
                package="jig_example",
                executable="py_echo_node",
                name="py_echo_node",
                namespace="py_echo_node",
                output="screen",
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestPubSub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_pub_sub")
        cls.qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def tearDown(self):
        # Ensure echo_node is active for other tests
        wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE, timeout=3.0)

    def _wait_active(self, name):
        self.assertTrue(
            wait_for_node_state(self.node, name, State.PRIMARY_STATE_ACTIVE),
            f"{name} did not reach ACTIVE",
        )

    def _wait_for_pub_match(self, pub, timeout=5.0):
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=timeout)
        while pub.get_subscription_count() == 0 and self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)

    def _publish_and_wait_echo(self, input_topic, output_topic, data, prefix):
        """Publish on input, wait for echo on output. Subscribe first to avoid race."""
        received = []
        sub = self.node.create_subscription(
            String,
            output_topic,
            lambda msg: received.append(msg),
            self.qos,
        )

        pub = self.node.create_publisher(String, input_topic, self.qos)
        self._wait_for_pub_match(pub)

        # Publish multiple times to handle potential message drops
        for _ in range(3):
            pub.publish(String(data=data))
            rclpy.spin_once(self.node, timeout_sec=0.1)

        # Wait for echo
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=TIMEOUT)
        while self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if any(data in m.data for m in received):
                break

        self.node.destroy_publisher(pub)
        self.node.destroy_subscription(sub)

        matching = [m for m in received if data in m.data]
        self.assertGreater(len(matching), 0, f"Expected echo of '{data}' on {output_topic}")
        self.assertIn(prefix, matching[0].data)

    def test_cpp_publish_and_receive(self):
        """Publish on echo_node/input, verify echo on echo_node/output."""
        self._wait_active("/echo_node/echo_node")
        self._publish_and_wait_echo("/echo_node/input", "/echo_node/output", "hello", "echo")

    def test_subscriber_drops_when_inactive(self):
        """Deactivate echo_node, publish, verify no echo, reactivate, verify echo resumes."""
        self._wait_active("/echo_node/echo_node")

        # Subscribe to output first
        received = []
        sub = self.node.create_subscription(
            String,
            "/echo_node/output",
            lambda msg: received.append(msg),
            self.qos,
        )
        pub = self.node.create_publisher(String, "/echo_node/input", self.qos)
        self._wait_for_pub_match(pub)

        # Deactivate
        self.assertTrue(transition_node(self.node, "/echo_node/echo_node", Transition.TRANSITION_DEACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_INACTIVE))

        # Clear received and publish while inactive
        received.clear()
        pub.publish(String(data="dropped"))
        msgs = collect_topic_messages(
            self.node,
            "/echo_node/output",
            String,
            duration=2.0,
            qos=self.qos,
        )
        echo_msgs = [m for m in msgs if "dropped" in m.data]
        self.assertEqual(len(echo_msgs), 0, "Should not receive echo while inactive")

        # Reactivate
        self.assertTrue(transition_node(self.node, "/echo_node/echo_node", Transition.TRANSITION_ACTIVATE))
        self._wait_active("/echo_node/echo_node")
        self._wait_for_pub_match(pub)

        received.clear()
        pub.publish(String(data="resumed"))

        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=TIMEOUT)
        while self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if any("resumed" in m.data for m in received):
                break

        self.assertTrue(
            any("resumed" in m.data for m in received),
            "Expected echo after reactivation",
        )

        self.node.destroy_publisher(pub)
        self.node.destroy_subscription(sub)

    def test_python_publish_and_receive(self):
        """Publish on py_echo_node/input, verify echo on py_echo_node/output."""
        self._wait_active("/py_echo_node/py_echo_node")
        self._publish_and_wait_echo("/py_echo_node/input", "/py_echo_node/output", "hello_py", "py")
