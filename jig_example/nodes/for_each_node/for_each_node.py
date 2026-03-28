from dataclasses import dataclass, field

from jig_example.for_each_node.interface import ForEachNodeSession, run

from std_msgs.msg import String

from jig import TransitionCallbackReturn


@dataclass
class MySession(ForEachNodeSession):
    latest_status: dict = field(default_factory=dict)


def make_status_callback(target_name: str):
    def status_callback(sn: MySession, msg: String):
        sn.latest_status[target_name] = msg.data
        # Aggregate and publish
        parts = [f"{k}={v}" for k, v in sorted(sn.latest_status.items())]
        out = String()
        out.data = "; ".join(parts)
        sn.publishers.aggregated_status.publish(out)

    return status_callback


def on_configure(sn: MySession) -> TransitionCallbackReturn:
    for name, sub in sn.subscribers.target_status.items():
        sub.set_callback(make_status_callback(name))
    return TransitionCallbackReturn.SUCCESS


if __name__ == "__main__":
    run(MySession, on_configure)
