from dataclasses import dataclass

from jig_example.lifecycle_node.interface import LifecycleNodeSession, run

from std_msgs.msg import Bool, String

from jig import TransitionCallbackReturn


@dataclass
class MySession(LifecycleNodeSession):
    pass


def heartbeat_callback(sn: MySession, msg: Bool):
    sn.logger.info(f"Heartbeat received: {msg.data}")


def on_configure(sn: MySession) -> TransitionCallbackReturn:
    sn.subscribers.heartbeat.set_callback(heartbeat_callback)
    sn.publishers.state_report.publish(String(data="configured"))
    return TransitionCallbackReturn.SUCCESS


def on_activate(sn: MySession) -> TransitionCallbackReturn:
    sn.publishers.state_report.publish(String(data="active"))
    return TransitionCallbackReturn.SUCCESS


def on_deactivate(sn: MySession) -> TransitionCallbackReturn:
    sn.publishers.state_report.publish(String(data="inactive"))
    return TransitionCallbackReturn.SUCCESS


def on_cleanup(sn: MySession) -> TransitionCallbackReturn:
    sn.publishers.state_report.publish(String(data="unconfigured"))
    return TransitionCallbackReturn.SUCCESS


if __name__ == "__main__":
    run(
        MySession,
        on_configure,
        on_activate=on_activate,
        on_deactivate=on_deactivate,
        on_cleanup=on_cleanup,
    )
