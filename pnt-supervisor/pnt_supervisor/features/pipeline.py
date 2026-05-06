"""Ordered feature extraction pipeline."""

from __future__ import annotations

from collections.abc import Sequence

from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.core.platform import PlatformConfig

from .base import FeatureExtractor
from .kinematics import KinematicFeatureExtractor
from .quality import QualityFeatureExtractor
from .recovery import RecoveryFeatureExtractor
from .timing import TimingFeatureExtractor


class FeaturePipeline:
    """Run feature extractors in one standard order."""

    def __init__(self, extractors: Sequence[FeatureExtractor]) -> None:
        self.extractors = list(extractors)

    @classmethod
    def default(cls, *, platform_config: PlatformConfig | None = None) -> "FeaturePipeline":
        return cls(
            [
                TimingFeatureExtractor(),
                QualityFeatureExtractor(),
                KinematicFeatureExtractor(platform_config=platform_config),
                RecoveryFeatureExtractor(),
            ]
        )

    def extract(self, obs: EpochObservation) -> FeatureVector:
        out = FeatureVector(t_sec=obs.t_sec)
        for extractor in self.extractors:
            out = extractor.extract(obs, out)
        return out
