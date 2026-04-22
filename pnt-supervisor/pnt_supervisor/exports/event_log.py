"""Event log helpers for replay exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TransitionEvent:
    """State transition event emitted by replay runner."""

    t_sec: float
    from_state: str
    to_state: str
    reason: str

    def to_row(self) -> dict[str, Any]:
        return {
            "t_sec": self.t_sec,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason": self.reason,
        }
