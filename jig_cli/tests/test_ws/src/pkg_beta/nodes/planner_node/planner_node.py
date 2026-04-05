"""Stub node for jig_cli tests."""

from dataclasses import dataclass

from pkg_beta.planner_node.interface import PlannerNodeSession, run

from jig import TransitionCallbackReturn


@dataclass
class Session(PlannerNodeSession["Session"]):
    pass


def on_configure(sn: Session) -> TransitionCallbackReturn:
    return TransitionCallbackReturn.SUCCESS


if __name__ == "__main__":
    run(Session, on_configure)
