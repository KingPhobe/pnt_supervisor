"""Base interfaces for observation adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from pnt_supervisor.core.models import EpochObservation


class ObservationAdapter(ABC):
    """Abstract adapter that yields normalized epoch observations."""

    @abstractmethod
    def reset(self) -> None:
        """Reset parser and adapter state before replaying observations."""

    @abstractmethod
    def iter_observations(self) -> Iterator[EpochObservation]:
        """Yield epoch observations from the configured source."""
