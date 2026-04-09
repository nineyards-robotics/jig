import message_filters

from lifecycle_msgs.msg import State

from .session import Session

from typing import Any, Callable, Generic, Optional, TypeVar

SessionT = TypeVar("SessionT", bound=Session)

Msg1T = TypeVar("Msg1T")
Msg2T = TypeVar("Msg2T")
Msg3T = TypeVar("Msg3T")
Msg4T = TypeVar("Msg4T")
Msg5T = TypeVar("Msg5T")
Msg6T = TypeVar("Msg6T")
Msg7T = TypeVar("Msg7T")
Msg8T = TypeVar("Msg8T")
Msg9T = TypeVar("Msg9T")


class _SyncGroupBase(Generic[SessionT]):
    """Base implementation for time-synchronised subscriber groups.

    Owns and creates message_filters.Subscriber instances internally.
    Provides lifecycle-guarded callback dispatch matching the jig entity pattern.
    """

    _subscribers: list[message_filters.Subscriber]
    _sync: Any  # TimeSynchronizer or ApproximateTimeSynchronizer
    _callback: Optional[Callable] = None

    def _initialise(
        self,
        session: SessionT,
        sync_class: type,
        queue_size: int,
        topics: list[tuple[type, str, Any]],
        *,
        slop: float | None = None,
    ) -> None:
        """Initialise the sync group.

        Args:
            session: The session instance (provides node reference).
            sync_class: message_filters.TimeSynchronizer or ApproximateTimeSynchronizer.
            queue_size: Size of the message queue per topic.
            topics: List of (msg_class, topic_name, qos_profile) tuples.
            slop: Maximum time difference in seconds (ApproximateTimeSynchronizer only).
        """
        self._subscribers = []
        for msg_class, topic_name, qos in topics:
            sub = message_filters.Subscriber(session.node, msg_class, topic_name, qos_profile=qos)
            self._subscribers.append(sub)

        sync_kwargs = {"queue_size": queue_size}
        if slop is not None:
            sync_kwargs["slop"] = slop
        self._sync = sync_class(self._subscribers, **sync_kwargs)

        def _guarded_callback(*msgs, _sn=session):
            if _sn.node.current_state != State.PRIMARY_STATE_ACTIVE:
                return
            if self._callback:
                self._callback(_sn, *msgs)

        self._sync.registerCallback(_guarded_callback)

    def _destroy(self, node) -> None:
        for sub in self._subscribers:
            sub.unregister()
        self._subscribers = []
        self._sync = None

    def set_callback(self, callback: Callable) -> None:
        self._callback = callback


class SyncGroup2(Generic[SessionT, Msg1T, Msg2T], _SyncGroupBase[SessionT]):
    _callback: Optional[Callable[[SessionT, Msg1T, Msg2T], None]] = None

    def set_callback(self, callback: Callable[[SessionT, Msg1T, Msg2T], None]) -> None:
        super().set_callback(callback)


class SyncGroup3(Generic[SessionT, Msg1T, Msg2T, Msg3T], _SyncGroupBase[SessionT]):
    _callback: Optional[Callable[[SessionT, Msg1T, Msg2T, Msg3T], None]] = None

    def set_callback(self, callback: Callable[[SessionT, Msg1T, Msg2T, Msg3T], None]) -> None:
        super().set_callback(callback)


class SyncGroup4(Generic[SessionT, Msg1T, Msg2T, Msg3T, Msg4T], _SyncGroupBase[SessionT]):
    _callback: Optional[Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T], None]] = None

    def set_callback(self, callback: Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T], None]) -> None:
        super().set_callback(callback)


class SyncGroup5(Generic[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T], _SyncGroupBase[SessionT]):
    _callback: Optional[Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T], None]] = None

    def set_callback(self, callback: Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T], None]) -> None:
        super().set_callback(callback)


class SyncGroup6(Generic[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T], _SyncGroupBase[SessionT]):
    _callback: Optional[Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T], None]] = None

    def set_callback(self, callback: Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T], None]) -> None:
        super().set_callback(callback)


class SyncGroup7(Generic[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T], _SyncGroupBase[SessionT]):
    _callback: Optional[Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T], None]] = None

    def set_callback(
        self, callback: Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T], None]
    ) -> None:
        super().set_callback(callback)


class SyncGroup8(Generic[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T, Msg8T], _SyncGroupBase[SessionT]):
    _callback: Optional[Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T, Msg8T], None]] = None

    def set_callback(
        self, callback: Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T, Msg8T], None]
    ) -> None:
        super().set_callback(callback)


class SyncGroup9(
    Generic[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T, Msg8T, Msg9T], _SyncGroupBase[SessionT]
):
    _callback: Optional[Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T, Msg8T, Msg9T], None]] = (
        None
    )

    def set_callback(
        self,
        callback: Callable[[SessionT, Msg1T, Msg2T, Msg3T, Msg4T, Msg5T, Msg6T, Msg7T, Msg8T, Msg9T], None],
    ) -> None:
        super().set_callback(callback)


__all__ = [
    "SyncGroup2",
    "SyncGroup3",
    "SyncGroup4",
    "SyncGroup5",
    "SyncGroup6",
    "SyncGroup7",
    "SyncGroup8",
    "SyncGroup9",
]
