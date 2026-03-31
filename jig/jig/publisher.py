from rclpy.event_handler import PublisherEventCallbacks, QoSLivelinessLostInfo, QoSOfferedDeadlineMissedInfo
from rclpy.publisher import Publisher as RclpyPublisher
from rclpy.qos import QoSProfile

from .session import Session

from typing import Callable, Generic, Optional, TypeVar

SessionT = TypeVar("SessionT", bound=Session)
MessageT = TypeVar("MessageT")


class Publisher(Generic[SessionT, MessageT]):
    _publisher: RclpyPublisher | None = None
    _deadline_callback: Optional[Callable[[SessionT, QoSOfferedDeadlineMissedInfo], None]] = None
    _liveliness_callback: Optional[Callable[[SessionT, QoSLivelinessLostInfo], None]] = None

    def _initialise(
        self,
        session: SessionT,
        msg_type: type[MessageT],
        topic_name: str,
        qos: QoSProfile | int,
    ) -> None:
        event_callbacks = PublisherEventCallbacks(
            deadline=lambda info: self._deadline_callback(session, info) if self._deadline_callback else None,
            liveliness=lambda info: self._liveliness_callback(session, info) if self._liveliness_callback else None,
        )

        self._publisher = session.node.create_publisher(
            msg_type=msg_type,
            topic=topic_name,
            qos_profile=qos,
            event_callbacks=event_callbacks,
        )

    def _destroy(self, node) -> None:
        if self._publisher is not None:
            node.destroy_publisher(self._publisher)
            self._publisher = None

    def publish(self, msg: MessageT) -> None:
        if self._publisher is None:
            raise RuntimeError("Can't publish. Publisher has not been initialised! This is an error in jig.")
        self._publisher.publish(msg)

    def publisher(self) -> RclpyPublisher:
        """Access underlying rclpy Publisher for advanced use."""
        if self._publisher is None:
            raise RuntimeError("Publisher has not been initialised! This is an error in jig.")
        return self._publisher

    def set_deadline_callback(self, callback: Callable[[SessionT, QoSOfferedDeadlineMissedInfo], None]):
        if self._publisher is None:
            raise RuntimeError(
                "Can't set deadline callback. Publisher has not been initialised! This is an error in jig."
            )
        self._deadline_callback = callback

    def set_liveliness_callback(self, callback: Callable[[SessionT, QoSLivelinessLostInfo], None]):
        if self._publisher is None:
            raise RuntimeError(
                "Can't set liveliness callback. Publisher has not been initialised! This is an error in jig."
            )
        self._liveliness_callback = callback


__all__ = ["Publisher"]
