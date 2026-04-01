from dataclasses import dataclass

from jig_example.py_sync_node.interface import PySyncNodeSession, run

from geometry_msgs.msg import PointStamped
from std_msgs.msg import String

from jig import TransitionCallbackReturn


@dataclass
class MySession(PySyncNodeSession["MySession"]):
    pass


def synced_callback(sn: MySession, a: PointStamped, b: PointStamped):
    out = String()
    out.data = f"synced: a=({a.point.x},{a.point.y}) b=({b.point.x},{b.point.y})"
    sn.publishers.output.publish(out)


def on_configure(sn: MySession) -> TransitionCallbackReturn:
    sn.subscribers.synced_points.set_callback(synced_callback)
    return TransitionCallbackReturn.SUCCESS


if __name__ == "__main__":
    run(MySession, on_configure)
