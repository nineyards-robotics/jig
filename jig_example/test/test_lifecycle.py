"""Tests for lifecycle management: autostart, manual transitions, state heartbeat, session reset."""

import time
import unittest

from helpers import (
    TIMEOUT,
    call_service,
    collect_topic_messages,
    state_qos,
    transition_node,
    wait_for_node_state,
    wait_for_topic_message,
)
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy

from lifecycle_msgs.msg import State, Transition
from std_msgs.msg import String

from lifecycle_msgs.srv import GetState


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
                executable="lifecycle_node",
                name="lifecycle_node",
                namespace="lifecycle_node",
                output="screen",
                parameters=[{"autostart": False}],
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


def _reset_to_unconfigured(node, name):
    """Drive a lifecycle node back to UNCONFIGURED from whatever state it's in."""
    resp = call_service(node, f"{name}/get_state", GetState, GetState.Request())
    if resp is None:
        return
    state_id = resp.current_state.id

    if state_id == State.PRIMARY_STATE_ACTIVE:
        transition_node(node, name, Transition.TRANSITION_DEACTIVATE)
        wait_for_node_state(node, name, State.PRIMARY_STATE_INACTIVE, timeout=5.0)
        transition_node(node, name, Transition.TRANSITION_CLEANUP)
        wait_for_node_state(node, name, State.PRIMARY_STATE_UNCONFIGURED, timeout=5.0)
    elif state_id == State.PRIMARY_STATE_INACTIVE:
        transition_node(node, name, Transition.TRANSITION_CLEANUP)
        wait_for_node_state(node, name, State.PRIMARY_STATE_UNCONFIGURED, timeout=5.0)


class TestLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_lifecycle")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def tearDown(self):
        # Reset lifecycle_node to UNCONFIGURED so tests are independent
        _reset_to_unconfigured(self.node, "/lifecycle_node/lifecycle_node")

    def test_autostart_activates(self):
        """echo_node (autostart=true) should reach ACTIVE."""
        self.assertTrue(
            wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE),
            "echo_node did not reach ACTIVE state",
        )

    def test_no_autostart_stays_unconfigured(self):
        """lifecycle_node (autostart=false) should be UNCONFIGURED."""
        self.assertTrue(
            wait_for_node_state(
                self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_UNCONFIGURED, timeout=5.0
            ),
            "lifecycle_node should be UNCONFIGURED",
        )

    def test_manual_configure_activate(self):
        """Drive lifecycle_node through configure -> activate manually."""
        self.assertTrue(
            wait_for_node_state(
                self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_UNCONFIGURED, timeout=5.0
            )
        )

        # Configure
        self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_CONFIGURE))
        self.assertTrue(wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_INACTIVE))

        # Verify state_report topic exists and has content (TRANSIENT_LOCAL)
        received = []
        sub = self.node.create_subscription(
            String,
            "/lifecycle_node/state_report",
            lambda msg: received.append(msg.data),
            state_qos(),
        )
        end = self.node.get_clock().now() + rclpy.duration.Duration(seconds=3.0)
        while self.node.get_clock().now() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if received:
                break
        self.assertGreater(len(received), 0, "Expected messages on state_report")
        self.node.destroy_subscription(sub)

        # Activate
        self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_ACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_ACTIVE))

    def test_deactivate_cleanup_cycle(self):
        """Full lifecycle: configure -> activate -> deactivate -> cleanup."""
        self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_CONFIGURE))
        self.assertTrue(wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_INACTIVE))

        self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_ACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_ACTIVE))

        self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_DEACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_INACTIVE))

        self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_CLEANUP))
        self.assertTrue(
            wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_UNCONFIGURED)
        )

    def test_state_heartbeat_published(self):
        """echo_node should publish state heartbeat on ~/state."""
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE))

        messages = collect_topic_messages(
            self.node,
            "/echo_node/echo_node/state",
            State,
            duration=2.0,
            qos=state_qos(),
        )
        self.assertGreater(len(messages), 0, "Expected state heartbeat messages")
        for msg in messages:
            self.assertEqual(msg.id, State.PRIMARY_STATE_ACTIVE)

    def test_session_reset_on_cleanup(self):
        """Full lifecycle cycle twice to verify session is properly destroyed and recreated."""
        for _ in range(2):
            self.assertTrue(
                transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_CONFIGURE)
            )
            self.assertTrue(
                wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_INACTIVE)
            )
            self.assertTrue(
                transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_ACTIVATE)
            )
            self.assertTrue(
                wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_ACTIVE)
            )
            self.assertTrue(
                transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_DEACTIVATE)
            )
            self.assertTrue(
                wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_INACTIVE)
            )
            self.assertTrue(transition_node(self.node, "/lifecycle_node/lifecycle_node", Transition.TRANSITION_CLEANUP))
            self.assertTrue(
                wait_for_node_state(self.node, "/lifecycle_node/lifecycle_node", State.PRIMARY_STATE_UNCONFIGURED)
            )
