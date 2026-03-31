# auto-generated DO NOT EDIT

from __future__ import annotations

from dataclasses import dataclass, field

import rclpy
from rclpy.client import Client
from rclpy.qos import (
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from lifecycle_msgs.srv import ChangeState
from std_msgs.msg import String

import jig

from typing import Callable, Generic, TypeVar

from .parameters import Params, ParamListener

SessionT = TypeVar("SessionT")


@dataclass
class Publishers(Generic[SessionT]):
    status: jig.Publisher[SessionT, String] = field(default_factory=jig.Publisher)


@dataclass
class Subscribers(Generic[SessionT]):
    node_states: dict[str, jig.Subscriber[SessionT, String]] = field(default_factory=dict)


@dataclass
class Services(Generic[SessionT]):
    pass


@dataclass
class ServiceClients:
    change_state_clients: dict[str, Client] = field(default_factory=dict)  # srv_type: lifecycle_msgs/srv/ChangeState


@dataclass
class Actions:
    pass


@dataclass
class ActionClients:
    pass


@dataclass
class ForEachParamSession(jig.Session[SessionT]):
    publishers: Publishers[SessionT]
    subscribers: Subscribers[SessionT]
    services: Services[SessionT]
    service_clients: ServiceClients
    actions: Actions
    action_clients: ActionClients

    param_listener: ParamListener
    params: Params


T = TypeVar("T", bound=ForEachParamSession)


class _ForEachParamNode(jig.BaseNode[T]):

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
            "for_each_param",
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
        sn.publishers.status._initialise(sn, String, f"/robot/{params.robot_id}/status", QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10, reliability=ReliabilityPolicy.RELIABLE))

        # initialise subscribers
        for key in params.managed_nodes:
            sn.subscribers.node_states[key] = jig.Subscriber()
            sn.subscribers.node_states[key]._initialise(sn, String, f"/{key}/state", QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10, reliability=ReliabilityPolicy.RELIABLE))
            jig.attach_default_qos_handlers(sn.subscribers.node_states[key])

        # initialise services

        # initialise for_each_param service clients: change_state_clients
        for key in params.managed_nodes:
            sn.service_clients.change_state_clients[key] = node.create_client(ChangeState, f"/{key}/change_state")

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
        for _key, sub in sn.subscribers.node_states.items():
            sub._destroy(sn.node)
        for _key, cli in sn.service_clients.change_state_clients.items():
            sn.node.destroy_client(cli)


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

    wrapper = _ForEachParamNode(
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
