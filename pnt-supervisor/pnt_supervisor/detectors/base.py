"""Detector base interface and shared helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector


def clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


class Detector(ABC):
    """Base class for all detectors."""

    name: str = "detector"

    @abstractmethod
    def evaluate(self, obs: EpochObservation, features: FeatureVector, config: Any) -> DetectorResult:
        """Evaluate detector using observation, extracted features and config."""
