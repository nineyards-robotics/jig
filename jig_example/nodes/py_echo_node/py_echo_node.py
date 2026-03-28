from dataclasses import dataclass

from jig_example.py_echo_node.interface import PyEchoNodeSession, run

from std_msgs.msg import String

from example_interfaces.srv import AddTwoInts, Trigger

import jig
from jig import TransitionCallbackReturn


@dataclass
class MySession(PyEchoNodeSession):
    counter: int = 0


def input_callback(sn: MySession, msg: String):
    out = String()
    out.data = f"{sn.params.message_prefix}: {msg.data}"
    sn.publishers.output.publish(out)


def add_two_ints_handler(
    sn: MySession, request: AddTwoInts.Request, response: AddTwoInts.Response
) -> AddTwoInts.Response:
    response.sum = request.a + request.b
    return response


def get_counter_handler(sn: MySession, request: Trigger.Request, response: Trigger.Response) -> Trigger.Response:
    response.success = True
    response.message = f"{sn.params.message_prefix}: counter={sn.counter}"
    return response


def timer_callback(sn: MySession):
    sn.counter += 1
    msg = String()
    msg.data = f"{sn.params.message_prefix}: {sn.counter}"
    sn.publishers.output.publish(msg)


def on_configure(sn: MySession) -> TransitionCallbackReturn:
    sn.subscribers.input.set_callback(input_callback)
    sn.services.add_two_ints.set_request_handler(add_two_ints_handler)
    sn.services.get_counter.set_request_handler(get_counter_handler)
    jig.create_timer(sn, sn.params.publish_rate_sec, timer_callback)
    return TransitionCallbackReturn.SUCCESS


if __name__ == "__main__":
    run(MySession, on_configure)
