"""Tests for default QoS handlers: deadline miss triggers deactivation."""

import time
import unittest

from helpers import TIMEOUT, transition_node, wait_for_node_state
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy
from rclpy.qos import Duration, HistoryPolicy, LivelinessPolicy, QoSProfile, ReliabilityPolicy

from lifecycle_msgs.msg import State, Transition
from std_msgs.msg import Bool


@pytest.mark.launch_test
def generate_test_description():
    return launch.LaunchDescription(
        [
            launch_ros.actions.Node(
                package="jig_example",
                executable="lifecycle_node",
                name="lifecycle_node",
                namespace="lifecycle_node",
                output="screen",
                parameters=[{"autostart": False}],
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestQosHandlers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_qos_handlers")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def test_deadline_miss_deactivates(self):
        """Activate lifecycle_node, publish heartbeats, stop, wait for deadline miss -> INACTIVE."""
        # Configure and activate
        self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_CONFIGURE))
        self.assertTrue(wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_INACTIVE))
        self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_ACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_ACTIVE))

        # Publish heartbeats matching the subscriber's QoS (deadline 500ms)
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            deadline=Duration(nanoseconds=500_000_000),
            liveliness=LivelinessPolicy.AUTOMATIC,
            liveliness_lease_duration=Duration(nanoseconds=500_000_000),
        )
        pub = self.node.create_publisher(Bool, "/lifecycle_node/heartbeat", qos)

        # Send heartbeats for 1 second
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=1.0)
        while self.node.get_clock().now() < end:
            pub.publish(Bool(data=True))
            rclpy.spin_once(self.node, timeout_sec=0.1)

        # Stop publishing — deadline miss should trigger after 500ms
        self.node.destroy_publisher(pub)

        # Wait for the node to deactivate due to deadline miss
        self.assertTrue(
            wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_INACTIVE, timeout=5.0),
            "lifecycle_node should deactivate on deadline miss",
        )
