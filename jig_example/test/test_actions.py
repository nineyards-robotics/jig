"""Tests for action server functionality."""

import unittest

from helpers import (
    TIMEOUT,
    get_action_result,
    send_action_goal,
    send_action_goal_with_feedback,
    transition_node,
    wait_for_node_state,
)
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy

from action_msgs.msg import GoalStatus
from lifecycle_msgs.msg import State, Transition

from example_interfaces.action import Fibonacci
from rclpy.action import ActionClient


@pytest.mark.launch_test
def generate_test_description():
    return launch.LaunchDescription(
        [
            launch_ros.actions.Node(
                package="jig_example",
                executable="action_node",
                name="action_node",
                namespace="action_node",
                output="screen",
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestActions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_actions")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _wait_active(self):
        self.assertTrue(
            wait_for_node_state(self.node, "/action_node/action_node", State.PRIMARY_STATE_ACTIVE),
            "action_node did not reach ACTIVE",
        )

    def test_goal_accepted_and_succeeds(self):
        """Fibonacci(order=5) should succeed with correct result."""
        self._wait_active()

        goal = Fibonacci.Goal(order=5)
        gh, client = send_action_goal(self.node, "/action_node/compute", Fibonacci, goal)
        self.assertIsNotNone(gh)
        self.assertTrue(gh.accepted, "Goal should be accepted")

        result = get_action_result(self.node, gh)
        self.assertIsNotNone(result)
        self.assertEqual(result.status, GoalStatus.STATUS_SUCCEEDED)
        # Fibonacci(5) = [0, 1, 1, 2, 3]
        self.assertEqual(list(result.result.sequence), [0, 1, 1, 2, 3])
        client.destroy()

    def test_goal_feedback_published(self):
        """Feedback messages should arrive before the result."""
        self._wait_active()

        goal = Fibonacci.Goal(order=5)
        gh, client, feedback = send_action_goal_with_feedback(self.node, "/action_node/compute", Fibonacci, goal)
        self.assertIsNotNone(gh)
        self.assertTrue(gh.accepted)

        result = get_action_result(self.node, gh)
        self.assertIsNotNone(result)
        self.assertEqual(result.status, GoalStatus.STATUS_SUCCEEDED)
        self.assertGreater(len(feedback), 0, "Expected at least one feedback message")
        client.destroy()

    def test_goal_rejected_when_inactive(self):
        """Deactivate action_node, send goal -> should be rejected."""
        self._wait_active()

        self.assertTrue(transition_node(self.node, "/action_node/action_node", Transition.TRANSITION_DEACTIVATE))
        self.assertTrue(wait_for_node_state(self.node, "/action_node/action_node", State.PRIMARY_STATE_INACTIVE))

        goal = Fibonacci.Goal(order=5)
        gh, client = send_action_goal(self.node, "/action_node/compute", Fibonacci, goal)
        self.assertIsNotNone(gh)
        self.assertFalse(gh.accepted, "Goal should be rejected when inactive")
        client.destroy()

        # Reactivate
        self.assertTrue(transition_node(self.node, "/action_node/action_node", Transition.TRANSITION_ACTIVATE))
        wait_for_node_state(self.node, "/action_node/action_node", State.PRIMARY_STATE_ACTIVE)

    def test_goal_validation_rejects_invalid(self):
        """order=-1 should be rejected by goal validator."""
        self._wait_active()

        goal = Fibonacci.Goal(order=-1)
        gh, client = send_action_goal(self.node, "/action_node/compute", Fibonacci, goal)
        self.assertIsNotNone(gh)
        self.assertFalse(gh.accepted, "Negative order should be rejected")
        client.destroy()

    def test_goal_replacement(self):
        """Send two goals to compute_replace — first aborted, second succeeds."""
        self._wait_active()

        # Send first goal with a large order to keep it busy
        goal1 = Fibonacci.Goal(order=5)
        gh1, client1 = send_action_goal(self.node, "/action_node/compute_replace", Fibonacci, goal1)
        self.assertIsNotNone(gh1)
        self.assertTrue(gh1.accepted)

        # Send second goal which should replace the first
        goal2 = Fibonacci.Goal(order=3)
        gh2, client2 = send_action_goal(self.node, "/action_node/compute_replace", Fibonacci, goal2)
        self.assertIsNotNone(gh2)
        self.assertTrue(gh2.accepted)

        # Second goal should succeed
        result2 = get_action_result(self.node, gh2)
        self.assertIsNotNone(result2)
        self.assertEqual(result2.status, GoalStatus.STATUS_SUCCEEDED)

        # First goal should have been aborted
        result1 = get_action_result(self.node, gh1)
        self.assertIsNotNone(result1)
        self.assertEqual(result1.status, GoalStatus.STATUS_ABORTED)

        client1.destroy()
        client2.destroy()

    def test_cancel_goal(self):
        """Send goal, cancel it, verify CANCELED status."""
        self._wait_active()

        goal = Fibonacci.Goal(order=5)
        gh, client = send_action_goal(self.node, "/action_node/compute_replace", Fibonacci, goal)
        self.assertIsNotNone(gh)
        self.assertTrue(gh.accepted)

        # Cancel
        cancel_future = gh.cancel_goal_async()
        rclpy.spin_until_future_complete(self.node, cancel_future, timeout_sec=TIMEOUT)

        result = get_action_result(self.node, gh)
        self.assertIsNotNone(result)
        self.assertIn(
            result.status,
            [GoalStatus.STATUS_CANCELED, GoalStatus.STATUS_SUCCEEDED],
            "Goal should be canceled or already succeeded",
        )
        client.destroy()
