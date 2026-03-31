# auto-generated DO NOT EDIT

from __future__ import annotations

from dataclasses import dataclass, field

import rclpy
from rclpy.qos import (
    DurabilityPolicy,
    Duration,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from std_msgs.msg import String

import jig

from typing import Callable, Generic, TypeVar

from .parameters import Params, ParamListener

SessionT = TypeVar("SessionT")


@dataclass
class Publishers(Generic[SessionT]):
    reliable_topic: jig.Publisher[SessionT, String] = field(default_factory=jig.Publisher)
    best_effort_topic: jig.Publisher[SessionT, String] = field(default_factory=jig.Publisher)


@dataclass
class Subscribers(Generic[SessionT]):
    keep_all_topic: jig.Subscriber[SessionT, String] = field(default_factory=jig.Subscriber)
    deadline_topic: jig.Subscriber[SessionT, String] = field(default_factory=jig.Subscriber)


@dataclass
class Services(Generic[SessionT]):
    pass


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
class QosCustomSession(jig.Session[SessionT]):
    publishers: Publishers[SessionT]
    subscribers: Subscribers[SessionT]
    services: Services[SessionT]
    service_clients: ServiceClients
    actions: Actions
    action_clients: ActionClients

    param_listener: ParamListener
    params: Params


T = TypeVar("T", bound=QosCustomSession)


class _QosCustomNode(jig.BaseNode[T]):

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
            "qos_custom",
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
        sn.publishers.reliable_topic._initialise(sn, String, "reliable_topic", QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.VOLATILE))
        sn.publishers.best_effort_topic._initialise(sn, String, "best_effort_topic", QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=5, reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.TRANSIENT_LOCAL))

        # initialise subscribers
        sn.subscribers.keep_all_topic._initialise(sn, String, "keep_all_topic", QoSProfile(history=HistoryPolicy.KEEP_ALL, reliability=ReliabilityPolicy.RELIABLE))
        jig.attach_default_qos_handlers(sn.subscribers.keep_all_topic)
        sn.subscribers.deadline_topic._initialise(sn, String, "deadline_topic", QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=20, reliability=ReliabilityPolicy.RELIABLE, deadline=Duration(nanoseconds=1000000000), lifespan=Duration(nanoseconds=500000000)))
        jig.attach_default_qos_handlers(sn.subscribers.deadline_topic)

        # initialise services

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
        sn.publishers.reliable_topic._destroy(sn.node)
        sn.publishers.best_effort_topic._destroy(sn.node)
        sn.subscribers.keep_all_topic._destroy(sn.node)
        sn.subscribers.deadline_topic._destroy(sn.node)


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

    wrapper = _QosCustomNode(
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
