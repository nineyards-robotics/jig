# auto-generated DO NOT EDIT

from __future__ import annotations

from dataclasses import dataclass, field

import rclpy
from rclpy.client import Client
from rclpy.action import ActionClient
from rclpy.qos import (
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from example_interfaces.action import Fibonacci
from example_interfaces.srv import AddTwoInts
from nav2_msgs.action import ComputePathToPose
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Bool
from std_msgs.msg import String
from std_srvs.srv import Trigger

import jig

from typing import Callable, TypeVar

from .parameters import Params, ParamListener


@dataclass
class Publishers:
    status: jig.Publisher[String] = field(default_factory=jig.Publisher[String])


@dataclass
class Subscribers:
    command: jig.Subscriber[Bool] = field(default_factory=jig.Subscriber[Bool])


@dataclass
class Services:
    reset: jig.Service[Trigger, Trigger.Request, Trigger.Response] = field(default_factory=jig.Service[Trigger, Trigger.Request, Trigger.Response])


@dataclass
class ServiceClients:
    compute: Client  # srv_type: example_interfaces/srv/AddTwoInts


@dataclass
class Actions:
    fibonacci_server: jig.SingleGoalActionServer[Fibonacci, Fibonacci.Goal, Fibonacci.Result, Fibonacci.Feedback]


@dataclass
class ActionClients:
    navigate: ActionClient  # action_type: nav2_msgs/action/NavigateToPose
    compute_path: ActionClient  # action_type: nav2_msgs/action/ComputePathToPose


@dataclass
class ActionClientsMixedSession(jig.Session):
    publishers: Publishers
    subscribers: Subscribers
    services: Services
    service_clients: ServiceClients
    actions: Actions
    action_clients: ActionClients

    param_listener: ParamListener
    params: Params


T = TypeVar("T", bound=ActionClientsMixedSession)


class _ActionClientsMixedNode(jig.BaseNode[T]):

    def __init__(
        self,
        session_type: type[T],
        on_configure: Callable[[T], jig.TransitionCallbackReturn],
        *,
        on_activate: Callable[[T], jig.TransitionCallbackReturn] | None = None,
        on_deactivate: Callable[[T], jig.TransitionCallbackReturn] | None = None,
        on_cleanup: Callable[[T], jig.TransitionCallbackReturn] | None = None,
        on_shutdown: Callable[[T], None] | None = None,
    ) -> None:
        super().__init__(
            "action_clients_mixed",
            session_type,
            on_configure,
            on_activate=on_activate,
            on_deactivate=on_deactivate,
            on_cleanup=on_cleanup,
            on_shutdown=on_shutdown,
        )

    def _create_session(self, node) -> T:
        # init parameters (must be before publishers/subscribers for param refs in names)
        param_listener = ParamListener(node)
        params = param_listener.get_params()

        # create publishers - using default constructors
        publishers = Publishers()

        # create subscribers - using default constructors
        subscribers = Subscribers()

        # create services - using default constructors
        services = Services()

        # initialise service clients
        service_clients = ServiceClients(
            compute=node.create_client(AddTwoInts, "/compute"),
        )

        # initialise actions
        actions = Actions(
            fibonacci_server=jig.SingleGoalActionServer[Fibonacci, Fibonacci.Goal, Fibonacci.Result, Fibonacci.Feedback](node, Fibonacci, "fibonacci_server"),
        )

        # initialise action clients
        action_clients = ActionClients(
            navigate=ActionClient(node, NavigateToPose, "/navigate"),
            compute_path=ActionClient(node, ComputePathToPose, "compute_path"),
        )

        sn = self._session_type(
            node=node,
            publishers=publishers,
            subscribers=subscribers,
            services=services,
            service_clients=service_clients,
            actions=actions,
            action_clients=action_clients,
            param_listener=param_listener,
            params=params,
        )

        # initialise publishers
        sn.publishers.status._initialise(sn, String, "/status", QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10, reliability=ReliabilityPolicy.RELIABLE))

        # initialise subscribers
        sn.subscribers.command._initialise(sn, Bool, "/command", QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=5, reliability=ReliabilityPolicy.BEST_EFFORT))
        jig.attach_default_qos_handlers(sn.subscribers.command)

        # initialise services
        sn.services.reset._initialise(sn, Trigger, "/reset")

        return sn

    def _activate_entities(self, sn: T) -> None:
        for timer in sn.timers:
            timer.reset()

    def _deactivate_entities(self, sn: T) -> None:
        for timer in sn.timers:
            timer.cancel()
        sn.actions.fibonacci_server.deactivate()

    def _destroy_entities(self, sn: T) -> None:
        for timer in sn.timers:
            sn.node.destroy_timer(timer)
        sn.timers.clear()
        sn.publishers.status._destroy(sn.node)
        sn.subscribers.command._destroy(sn.node)
        sn.services.reset._destroy(sn.node)
        sn.node.destroy_client(sn.service_clients.compute)
        sn.actions.fibonacci_server._destroy(sn.node)
        sn.action_clients.navigate.destroy()
        sn.action_clients.compute_path.destroy()


def run(
    session_type: type[T],
    on_configure: Callable[[T], jig.TransitionCallbackReturn],
    *,
    on_activate: Callable[[T], jig.TransitionCallbackReturn] | None = None,
    on_deactivate: Callable[[T], jig.TransitionCallbackReturn] | None = None,
    on_cleanup: Callable[[T], jig.TransitionCallbackReturn] | None = None,
    on_shutdown: Callable[[T], None] | None = None,
):

    rclpy.init()

    wrapper = _ActionClientsMixedNode(
        session_type,
        on_configure,
        on_activate=on_activate,
        on_deactivate=on_deactivate,
        on_cleanup=on_cleanup,
        on_shutdown=on_shutdown,
    )

    try:
        rclpy.spin(wrapper.node)
    except KeyboardInterrupt:
        # note rclpy installs signal handlers during rclpy.init() that respond to SIGINT (Ctrl+C) and shutdown the
        # context so no logging or anything should be done here.
        pass
    finally:
        wrapper.node.destroy_node()
        if rclpy.ok():
            # since the context is _probably_ shutdown already here, we are doing this just to be certain
            rclpy.shutdown()
