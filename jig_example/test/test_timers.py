"""Tests for timer functionality."""

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
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestTimers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_timers")
        cls.qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _ensure_active(self):
        """Ensure echo_node is active (may have been deactivated by a previous test)."""
        self.assertTrue(
            wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE),
            "echo_node did not reach ACTIVE",
        )

    def test_timer_fires_when_active(self):
        """Output topic receives periodic timer messages when active."""
        self._ensure_active()

        messages = collect_topic_messages(
            self.node,
            "/echo_node/output",
            String,
            duration=2.0,
            qos=self.qos,
        )
        # At 100ms rate, expect ~20 messages in 2s (allow some slack)
        self.assertGreater(len(messages), 5, "Expected periodic timer messages")

    def test_timer_stops_on_deactivate(self):
        """Deactivate echo_node, verify no new timer messages."""
        self._ensure_active()

        self.assertTrue(transition_node(self.node, "/echo_node/echo_node", Transition.TRANSITION_DEACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_INACTIVE))

        messages = collect_topic_messages(
            self.node,
            "/echo_node/output",
            String,
            duration=1.0,
            qos=self.qos,
        )
        self.assertEqual(len(messages), 0, "Timer should not fire when inactive")

        # Reactivate for other tests
        self.assertTrue(transition_node(self.node, "/echo_node/echo_node", Transition.TRANSITION_ACTIVATE))

    def test_timer_resumes_on_reactivate(self):
        """Deactivate then reactivate — timer messages should resume."""
        self._ensure_active()

        self.assertTrue(transition_node(self.node, "/echo_node/echo_node", Transition.TRANSITION_DEACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_INACTIVE))

        self.assertTrue(transition_node(self.node, "/echo_node/echo_node", Transition.TRANSITION_ACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE))

        messages = collect_topic_messages(
            self.node,
            "/echo_node/output",
            String,
            duration=2.0,
            qos=self.qos,
        )
        self.assertGreater(len(messages), 5, "Timer should resume after reactivation")
