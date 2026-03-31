from dataclasses import dataclass, field

from rclpy.lifecycle import LifecycleNode
from rclpy.timer import Timer

from typing import Generic, TypeVar

_SessionT = TypeVar("_SessionT")


@dataclass(kw_only=True)
class Session(Generic[_SessionT]):
    node: LifecycleNode
    timers: list[Timer] = field(default_factory=list)

    @property
    def logger(self):
        return self.node.get_logger()


__all__ = ["Session"]
