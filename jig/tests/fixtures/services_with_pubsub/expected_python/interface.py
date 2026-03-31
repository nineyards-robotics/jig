# auto-generated DO NOT EDIT

from __future__ import annotations

from dataclasses import dataclass, field

import rclpy
from rclpy.qos import (
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from example_interfaces.srv import AddTwoInts
from std_msgs.msg import String
from std_srvs.srv import Trigger

import jig

from typing import Callable, Generic, TypeVar

from .parameters import Params, ParamListener

SessionT = TypeVar("SessionT")


@dataclass
class Publishers(Generic[SessionT]):
    status: jig.Publisher[SessionT, String] = field(default_factory=jig.Publisher)


@dataclass
class Subscribers(Generic[SessionT]):
    command: jig.Subscriber[SessionT, String] = field(default_factory=jig.Subscriber)


@dataclass
class Services(Generic[SessionT]):
    reset: jig.Service[SessionT, Trigger, Trigger.Request, Trigger.Response] = field(default_factory=jig.Service)
    compute: jig.Service[SessionT, AddTwoInts, AddTwoInts.Request, AddTwoInts.Response] = field(default_factory=jig.Service)
    private_status: jig.Service[SessionT, Trigger, Trigger.Request, Trigger.Response] = field(default_factory=jig.Service)


@dataclass
class ServiceClients:
    pass


@dataclass
class Actions:
    pass


@dataclass
class ActionClients:
    pass


@dataclass
class ServicesWithPubsubSession(jig.Session, Generic[SessionT]):
    publishers: Publishers[SessionT]
    subscribers: Subscribers[SessionT]
    services: Services[SessionT]
    service_clients: ServiceClients
    actions: Actions
    action_clients: ActionClients

    param_listener: ParamListener
    params: Params


T = TypeVar("T", bound=ServicesWithPubsubSession)


class _ServicesWithPubsubNode(jig.BaseNode[T]):

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
            "services_with_pubsub",
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
        service_clients = ServiceClients()

        # initialise actions
        actions = Actions()

        # initialise action clients
        action_clients = ActionClients()

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
        sn.subscribers.command._initialise(sn, String, "/command", QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=5, reliability=ReliabilityPolicy.BEST_EFFORT))
        jig.attach_default_qos_handlers(sn.subscribers.command)

        # initialise services
        sn.services.reset._initialise(sn, Trigger, "/reset")
        sn.services.compute._initialise(sn, AddTwoInts, "compute")
        sn.services.private_status._initialise(sn, Trigger, "~/private_status")

        return sn

    def _activate_entities(self, sn: T) -> None:
        for timer in sn.timers:
            timer.reset()

    def _deactivate_entities(self, sn: T) -> None:
        for timer in sn.timers:
            timer.cancel()

    def _destroy_entities(self, sn: T) -> None:
        for timer in sn.timers:
            sn.node.destroy_timer(timer)
        sn.timers.clear()
        sn.publishers.status._destroy(sn.node)
        sn.subscribers.command._destroy(sn.node)
        sn.services.reset._destroy(sn.node)
        sn.services.compute._destroy(sn.node)
        sn.services.private_status._destroy(sn.node)


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

    wrapper = _ServicesWithPubsubNode(
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
