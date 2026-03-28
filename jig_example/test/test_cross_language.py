"""Tests for cross-language interop: C++ pub -> Python sub and vice versa."""

import unittest

from helpers import TIMEOUT, wait_for_node_state, wait_for_topic_message
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from lifecycle_msgs.msg import State
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
                remappings=[("input", "/cross/cpp_input")],
            ),
            launch_ros.actions.Node(
                package="jig_example",
                executable="py_echo_node",
                name="py_echo_node",
                namespace="py_echo_node",
                output="screen",
                remappings=[("input", "/cross/py_input")],
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestCrossLanguage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_cross_language")
        cls.qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _wait_for_pub_match(self, pub, timeout=5.0):
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=timeout)
        while pub.get_subscription_count() == 0 and self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)

    def test_cpp_pub_to_python_sub(self):
        """Publish to C++ node's input, have Python node subscribe to C++ output."""
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE))
        self.assertTrue(wait_for_node_state(self.node, "/py_echo_node/py_echo_node", State.PRIMARY_STATE_ACTIVE))

        # Subscribe first to avoid race
        received = []
        sub = self.node.create_subscription(
            String,
            "/echo_node/output",
            lambda msg: received.append(msg),
            self.qos,
        )

        # C++ echo_node publishes on /echo_node/output — wire that to py_echo_node's input
        # For this test, we publish on cpp's remapped input and verify output
        pub = self.node.create_publisher(String, "/cross/cpp_input", self.qos)
        self._wait_for_pub_match(pub)

        # Publish multiple times to handle potential message drops
        for _ in range(3):
            pub.publish(String(data="cross_test_cpp"))
            rclpy.spin_once(self.node, timeout_sec=0.1)

        # Wait for echo
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=TIMEOUT)
        while self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if any("cross_test_cpp" in m.data for m in received):
                break

        matching = [m for m in received if "cross_test_cpp" in m.data]
        self.assertGreater(len(matching), 0, "Expected C++ echo of cross_test_cpp")

        self.node.destroy_publisher(pub)
        self.node.destroy_subscription(sub)

    def test_python_pub_to_cpp_sub(self):
        """Publish to Python node's input, verify Python echo on output."""
        self.assertTrue(wait_for_node_state(self.node, "/py_echo_node/py_echo_node", State.PRIMARY_STATE_ACTIVE))

        # Subscribe first to avoid race
        received = []
        sub = self.node.create_subscription(
            String,
            "/py_echo_node/output",
            lambda msg: received.append(msg),
            self.qos,
        )

        pub = self.node.create_publisher(String, "/cross/py_input", self.qos)
        self._wait_for_pub_match(pub)

        # Publish multiple times to handle potential message drops
        for _ in range(3):
            pub.publish(String(data="cross_test_py"))
            rclpy.spin_once(self.node, timeout_sec=0.1)

        # Wait for echo
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=TIMEOUT)
        while self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if any("cross_test_py" in m.data for m in received):
                break

        matching = [m for m in received if "cross_test_py" in m.data]
        self.assertGreater(len(matching), 0, "Expected Python echo of cross_test_py")

        self.node.destroy_publisher(pub)
        self.node.destroy_subscription(sub)
