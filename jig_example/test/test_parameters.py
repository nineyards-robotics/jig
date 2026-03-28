"""Tests for parameter functionality: overrides, read-only enforcement, substitution."""

import unittest

from helpers import TIMEOUT, call_service, wait_for_node_state, wait_for_topic_message
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy

from lifecycle_msgs.msg import State
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from std_msgs.msg import String

from example_interfaces.srv import Trigger
from rcl_interfaces.srv import SetParameters


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
                parameters=[{"message_prefix": "TEST"}],
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


class TestParameters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_parameters")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def test_parameter_override_applied(self):
        """get_counter response should contain 'TEST' prefix."""
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE))

        resp = call_service(self.node, "/echo_node/get_counter", Trigger, Trigger.Request())
        self.assertIsNotNone(resp)
        self.assertIn("TEST", resp.message, "Expected TEST prefix in counter response")

    def test_read_only_param_rejected(self):
        """Setting a read-only parameter should fail."""
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE))

        req = SetParameters.Request()
        req.parameters = [
            Parameter(
                name="message_prefix",
                value=ParameterValue(
                    type=ParameterType.PARAMETER_STRING,
                    string_value="CHANGED",
                ),
            )
        ]
        resp = call_service(self.node, "/echo_node/echo_node/set_parameters", SetParameters, req)
        self.assertIsNotNone(resp)
        # Read-only params should reject the change
        self.assertFalse(
            resp.results[0].successful,
            "Setting read-only param should fail",
        )

    def test_param_substitution_in_topic_name(self):
        """Topic TEST/prefixed_output should exist (resolved from ${param:message_prefix})."""
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE))

        msg = wait_for_topic_message(
            self.node,
            "/echo_node/TEST/prefixed_output",
            String,
            timeout=5.0,
        )
        # The topic should exist — timer publishes on output, and input callback
        # also publishes on prefixed_output. Just verify the topic is reachable.
        # We may or may not get a message depending on timing, but at minimum
        # the topic should be discoverable. Let's check via node graph.
        topic_names = [t[0] for t in self.node.get_topic_names_and_types()]
        self.assertIn(
            "/echo_node/TEST/prefixed_output",
            topic_names,
            "Expected param-substituted topic to exist",
        )

    def test_param_substitution_in_qos(self):
        """Node configures successfully with param-driven QoS (queue_depth)."""
        # If the node reached ACTIVE, param substitution in QoS worked
        self.assertTrue(
            wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_ACTIVE),
            "Node should configure successfully with param-substituted QoS",
        )
