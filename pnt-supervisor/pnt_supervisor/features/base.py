"""Shared feature extraction primitives."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Deque

from pnt_supervisor.core.models import EpochObservation

if TYPE_CHECKING:
    from pnt_supervisor.core.models import FeatureVector


@dataclass(slots=True)
class FeatureContext:
    """Rolling state for feature extractors."""

    maxlen: int = 60
    observations: Deque[EpochObservation] = field(init=False)

    def __post_init__(self) -> None:
        self.observations = deque(maxlen=self.maxlen)

    @property
    def last_observation(self) -> EpochObservation | None:
        return self.observations[-1] if self.observations else None

    def append(self, obs: EpochObservation) -> None:
        self.observations.append(obs)


class FeatureExtractor(ABC):
    """Base class for all feature extractors."""

    def __init__(self, *, window_size: int = 60) -> None:
        self.context = FeatureContext(maxlen=window_size)

    @abstractmethod
    def extract(self, obs: EpochObservation, out: FeatureVector) -> FeatureVector:
        """Update rolling state and emit partial feature values."""
