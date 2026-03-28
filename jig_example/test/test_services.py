"""Tests for service server functionality."""

import unittest

from helpers import TIMEOUT, call_service, transition_node, wait_for_node_state
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy

from lifecycle_msgs.msg import State, Transition

from example_interfaces.srv import AddTwoInts, Trigger


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


class TestServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_services")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _wait_active(self, name):
        self.assertTrue(
            wait_for_node_state(self.node, name, State.PRIMARY_STATE_ACTIVE),
            f"{name} did not reach ACTIVE",
        )

    def test_add_two_ints_cpp(self):
        """Call echo_node/add_two_ints(3, 7), verify sum=10."""
        self._wait_active("/echo_node/echo_node")

        req = AddTwoInts.Request()
        req.a = 3
        req.b = 7
        resp = call_service(self.node, "/echo_node/add_two_ints", AddTwoInts, req)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.sum, 10)

    def test_get_counter_cpp(self):
        """Call echo_node/get_counter, verify response contains counter."""
        self._wait_active("/echo_node/echo_node")

        resp = call_service(self.node, "/echo_node/get_counter", Trigger, Trigger.Request())
        self.assertIsNotNone(resp)
        self.assertTrue(resp.success)
        self.assertIn("counter=", resp.message)

    def test_service_rejected_when_inactive(self):
        """Deactivate echo_node, call service, verify default/empty response."""
        self._wait_active("/echo_node/echo_node")

        # Deactivate
        self.assertTrue(transition_node(self.node, "/echo_node/echo_node", Transition.TRANSITION_DEACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/echo_node/echo_node", State.PRIMARY_STATE_INACTIVE))

        # Call service while inactive — jig returns default response
        req = AddTwoInts.Request()
        req.a = 3
        req.b = 7
        resp = call_service(self.node, "/echo_node/add_two_ints", AddTwoInts, req)
        self.assertIsNotNone(resp)
        # Default response has sum=0 (service handler not called)
        self.assertEqual(resp.sum, 0)

        # Reactivate for other tests
        self.assertTrue(transition_node(self.node, "/echo_node/echo_node", Transition.TRANSITION_ACTIVATE))
        self._wait_active("/echo_node/echo_node")

    def test_add_two_ints_python(self):
        """Call py_echo_node/add_two_ints(5, 8), verify sum=13."""
        self._wait_active("/py_echo_node/py_echo_node")

        req = AddTwoInts.Request()
        req.a = 5
        req.b = 8
        resp = call_service(self.node, "/py_echo_node/add_two_ints", AddTwoInts, req)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.sum, 13)
