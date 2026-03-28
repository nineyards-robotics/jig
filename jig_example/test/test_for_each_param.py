"""Tests for for_each_param dynamic entity creation."""

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
                executable="for_each_node",
                name="for_each_node",
                namespace="for_each_node",
                output="screen",
                parameters=[{"target_nodes": ["alpha", "beta"]}],
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestForEachParam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_for_each_param")
        cls.qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _wait_active(self):
        self.assertTrue(
            wait_for_node_state(self.node, "/for_each_node/for_each_node", State.PRIMARY_STATE_ACTIVE),
            "for_each_node did not reach ACTIVE",
        )

    def test_dynamic_subscribers_created(self):
        """Topics /alpha/status and /beta/status should have subscribers."""
        self._wait_active()

        # Check that the topics have subscribers by looking at subscription count
        pub_alpha = self.node.create_publisher(String, "/for_each_node/alpha/status", self.qos)
        pub_beta = self.node.create_publisher(String, "/for_each_node/beta/status", self.qos)

        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=5.0)
        while (
            pub_alpha.get_subscription_count() == 0 or pub_beta.get_subscription_count() == 0
        ) and self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertGreater(
            pub_alpha.get_subscription_count(),
            0,
            "Expected subscriber on alpha/status",
        )
        self.assertGreater(
            pub_beta.get_subscription_count(),
            0,
            "Expected subscriber on beta/status",
        )
        self.node.destroy_publisher(pub_alpha)
        self.node.destroy_publisher(pub_beta)

    def test_dynamic_subscriber_receives(self):
        """Publish on /alpha/status, verify aggregated output is published."""
        self._wait_active()

        # Subscribe first to avoid race
        received = []
        sub = self.node.create_subscription(
            String,
            "/for_each_node/bot1/aggregated_status",
            lambda msg: received.append(msg),
            self.qos,
        )

        pub = self.node.create_publisher(String, "/for_each_node/alpha/status", self.qos)

        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=5.0)
        while pub.get_subscription_count() == 0 and self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        # Publish multiple times to handle potential message drops
        for _ in range(3):
            pub.publish(String(data="ok"))
            rclpy.spin_once(self.node, timeout_sec=0.1)

        # Wait for aggregated message
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=TIMEOUT)
        while self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if any("alpha=ok" in m.data for m in received):
                break

        matching = [m for m in received if "alpha=ok" in m.data]
        self.assertGreater(len(matching), 0, "Expected aggregated status containing alpha=ok")

        self.node.destroy_publisher(pub)
        self.node.destroy_subscription(sub)
