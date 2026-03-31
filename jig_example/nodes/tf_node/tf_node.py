from dataclasses import dataclass

from jig_example.tf_node.interface import TfNodeSession, run

from geometry_msgs.msg import TransformStamped

from std_srvs.srv import Trigger

import jig
from jig import TransitionCallbackReturn


@dataclass
class MySession(TfNodeSession["MySession"]):
    pass


def on_configure(sn: MySession) -> TransitionCallbackReturn:
    # Broadcast a static transform: world -> base_link at (1.0, 2.0, 3.0)
    static_tf = TransformStamped()
    static_tf.header.stamp = sn.node.get_clock().now().to_msg()
    static_tf.header.frame_id = "world"
    static_tf.child_frame_id = "base_link"
    static_tf.transform.translation.x = 1.0
    static_tf.transform.translation.y = 2.0
    static_tf.transform.translation.z = 3.0
    static_tf.transform.rotation.w = 1.0
    sn.tf_static_broadcaster.sendTransform(static_tf)

    # Set up a timer that broadcasts: base_link -> sensor at (0.1, 0.2, 0.3)
    def broadcast_dynamic(sn: MySession):
        tf_msg = TransformStamped()
        tf_msg.header.stamp = sn.node.get_clock().now().to_msg()
        tf_msg.header.frame_id = "base_link"
        tf_msg.child_frame_id = "sensor"
        tf_msg.transform.translation.x = 0.1
        tf_msg.transform.translation.y = 0.2
        tf_msg.transform.translation.z = 0.3
        tf_msg.transform.rotation.w = 1.0
        sn.tf_broadcaster.sendTransform(tf_msg)

    jig.create_timer(sn, 0.1, broadcast_dynamic)

    # Service handler: look up the chained transform world -> sensor
    def handle_lookup(sn: MySession, _req: Trigger.Request, resp: Trigger.Response):
        try:
            from rclpy.time import Time

            t = sn.tf_buffer.lookup_transform("world", "sensor", Time())
            tx = t.transform.translation
            resp.success = True
            resp.message = f"{tx.x:.1f},{tx.y:.1f},{tx.z:.1f}"
        except Exception as e:
            resp.success = False
            resp.message = str(e)
        return resp

    sn.services.lookup_transform.set_request_handler(handle_lookup)

    return TransitionCallbackReturn.SUCCESS


if __name__ == "__main__":
    run(MySession, on_configure)
