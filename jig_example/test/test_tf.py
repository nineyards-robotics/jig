"""Tests for TF2 transform support (listener, broadcaster, static broadcaster)."""

import unittest

from helpers import TIMEOUT, call_service, wait_for_node_state, wait_for_topic_message
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import pytest
import rclpy
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from lifecycle_msgs.msg import State
from tf2_msgs.msg import TFMessage

from std_srvs.srv import Trigger

TF_NODE = "/tf_node/tf_node"


def tf_static_qos():
    """QoS profile matching /tf_static (transient local, reliable)."""
    return QoSProfile(
        history=HistoryPolicy.KEEP_ALL,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
    )


@pytest.mark.launch_test
def generate_test_description():
    return launch.LaunchDescription(
        [
            launch_ros.actions.Node(
                package="jig_example",
                executable="tf_node",
                name="tf_node",
                namespace="tf_node",
                output="screen",
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestTf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_tf")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _wait_active(self):
        self.assertTrue(
            wait_for_node_state(self.node, TF_NODE, State.PRIMARY_STATE_ACTIVE),
            "tf_node did not reach ACTIVE",
        )

    def test_static_broadcaster_publishes(self):
        """Verify the static transform world->base_link appears on /tf_static."""
        self._wait_active()

        msg = wait_for_topic_message(
            self.node,
            "/tf_static",
            TFMessage,
            timeout=TIMEOUT,
            qos=tf_static_qos(),
            predicate=lambda m: any(
                t.header.frame_id == "world" and t.child_frame_id == "base_link" for t in m.transforms
            ),
        )
        self.assertIsNotNone(msg, "Did not receive static transform on /tf_static")

        tf = next(t for t in msg.transforms if t.header.frame_id == "world" and t.child_frame_id == "base_link")
        self.assertAlmostEqual(tf.transform.translation.x, 1.0)
        self.assertAlmostEqual(tf.transform.translation.y, 2.0)
        self.assertAlmostEqual(tf.transform.translation.z, 3.0)

    def test_dynamic_broadcaster_publishes(self):
        """Verify the dynamic transform base_link->sensor appears on /tf."""
        self._wait_active()

        msg = wait_for_topic_message(
            self.node,
            "/tf",
            TFMessage,
            timeout=TIMEOUT,
            qos=10,
            predicate=lambda m: any(
                t.header.frame_id == "base_link" and t.child_frame_id == "sensor" for t in m.transforms
            ),
        )
        self.assertIsNotNone(msg, "Did not receive dynamic transform on /tf")

        tf = next(t for t in msg.transforms if t.header.frame_id == "base_link" and t.child_frame_id == "sensor")
        self.assertAlmostEqual(tf.transform.translation.x, 0.1)
        self.assertAlmostEqual(tf.transform.translation.y, 0.2)
        self.assertAlmostEqual(tf.transform.translation.z, 0.3)

    def test_listener_chained_lookup(self):
        """Call the lookup service to resolve world->sensor (chained via base_link).

        This exercises the full round trip:
        - static_broadcaster publishes world->base_link
        - broadcaster publishes base_link->sensor
        - listener populates the buffer from /tf and /tf_static
        - buffer.lookup_transform resolves the chain world->sensor
        """
        self._wait_active()

        # Give the node time to broadcast a few dynamic transforms so the buffer is populated
        rclpy.spin_once(self.node, timeout_sec=1.0)

        resp = call_service(
            self.node,
            f"{TF_NODE}/lookup_transform",
            Trigger,
            Trigger.Request(),
        )
        self.assertIsNotNone(resp, "lookup_transform service did not respond")
        self.assertTrue(resp.success, f"lookup_transform failed: {resp.message}")

        # The chained transform world->sensor should be (1.0+0.1, 2.0+0.2, 3.0+0.3)
        x, y, z = (float(v) for v in resp.message.split(","))
        self.assertAlmostEqual(x, 1.1, places=1)
        self.assertAlmostEqual(y, 2.2, places=1)
        self.assertAlmostEqual(z, 3.3, places=1)
