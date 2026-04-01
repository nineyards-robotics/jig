"""Tests for message synchronisation (sync groups)."""

import unittest

from helpers import TIMEOUT, wait_for_node_state, wait_for_topic_message
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from geometry_msgs.msg import PointStamped
from lifecycle_msgs.msg import State
from std_msgs.msg import String


@pytest.mark.launch_test
def generate_test_description():
    return launch.LaunchDescription(
        [
            launch_ros.actions.Node(
                package="jig_example",
                executable="sync_node",
                name="sync_node",
                namespace="sync_node",
                output="screen",
            ),
            launch_ros.actions.Node(
                package="jig_example",
                executable="py_sync_node",
                name="py_sync_node",
                namespace="py_sync_node",
                output="screen",
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_sync")
        cls.qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _wait_active(self, name):
        self.assertTrue(
            wait_for_node_state(self.node, name, State.PRIMARY_STATE_ACTIVE),
            f"{name} did not reach ACTIVE",
        )

    def _publish_synced_points(self, namespace, x_a, y_a, x_b, y_b):
        """Publish two PointStamped messages with the same timestamp."""
        pub_a = self.node.create_publisher(PointStamped, f"{namespace}/point_a", self.qos)
        pub_b = self.node.create_publisher(PointStamped, f"{namespace}/point_b", self.qos)

        # Wait for subscriptions to match
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=5.0)
        while (
            pub_a.get_subscription_count() == 0 or pub_b.get_subscription_count() == 0
        ) and self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        now = self.node.get_clock().now().to_msg()

        msg_a = PointStamped()
        msg_a.header.stamp = now
        msg_a.header.frame_id = "test"
        msg_a.point.x = float(x_a)
        msg_a.point.y = float(y_a)

        msg_b = PointStamped()
        msg_b.header.stamp = now
        msg_b.header.frame_id = "test"
        msg_b.point.x = float(x_b)
        msg_b.point.y = float(y_b)

        pub_a.publish(msg_a)
        pub_b.publish(msg_b)

        return pub_a, pub_b

    def _test_sync_node(self, namespace):
        """Test that a sync node publishes a combined output."""
        self._wait_active(f"{namespace}/{namespace}")

        pub_a, pub_b = self._publish_synced_points(namespace, 1.0, 2.0, 3.0, 4.0)

        msg = wait_for_topic_message(
            self.node,
            f"{namespace}/output",
            String,
            timeout=TIMEOUT,
            qos=self.qos,
            predicate=lambda m: "synced:" in m.data,
        )

        self.node.destroy_publisher(pub_a)
        self.node.destroy_publisher(pub_b)

        self.assertIsNotNone(msg, f"Did not receive synced output from {namespace}")
        self.assertIn("synced:", msg.data)

    def test_cpp_sync_node(self):
        """C++ sync node delivers paired messages through sync callback."""
        self._test_sync_node("sync_node")

    def test_python_sync_node(self):
        """Python sync node delivers paired messages through sync callback."""
        self._test_sync_node("py_sync_node")
