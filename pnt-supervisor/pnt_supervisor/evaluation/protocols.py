"""Protocols for evaluation pipeline collaborators."""

from __future__ import annotations

from typing import Any, Protocol

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector


class DetectorLike(Protocol):
    detector_name: str

    def evaluate(
        self,
        obs: EpochObservation,
        features: FeatureVector,
        config: Any | None = None,
    ) -> DetectorResult:
        ...
