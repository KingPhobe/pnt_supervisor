"""Factories for ReplayRunner's default feature pipeline and detectors."""

from __future__ import annotations

from typing import Any

from pnt_supervisor.detectors import (
    HardGatesDetector,
    KinematicAnomalyDetector,
    ModeFlapDetector,
    StaleDataDetector,
    SpeedAccelConsistencyConfig,
    SpeedAccelConsistencyDetector,
    StatisticalDetector,
    TimeConsistencyConfig,
    TimeConsistencyDetector,
)
from pnt_supervisor.features import FeaturePipeline, TimeConsistencyFeatureExtractor

from .protocols import DetectorLike


def build_default_feature_pipeline(config: Any | None = None) -> FeaturePipeline:
    extractors = list(FeaturePipeline.default().extractors)
    extractors.append(
        TimeConsistencyFeatureExtractor(
            window_s=getattr(getattr(config, "time_consistency", None), "window_s", 10.0),
            min_samples=getattr(getattr(config, "time_consistency", None), "min_samples", 5),
        )
    )
    return FeaturePipeline(extractors)


def build_default_detectors(config: Any | None = None) -> list[DetectorLike]:
    detectors: list[DetectorLike] = [
        HardGatesDetector(),
        KinematicAnomalyDetector(),
        StaleDataDetector(),
        ModeFlapDetector(),
        StatisticalDetector(),
    ]

    sac_cfg = getattr(config, "speed_accel_consistency", None)
    if sac_cfg is not None and getattr(sac_cfg, "enabled", False):
        detectors.append(
            SpeedAccelConsistencyDetector(
                SpeedAccelConsistencyConfig(**sac_cfg.model_dump())
            )
        )

    tc_cfg = getattr(config, "time_consistency", None)
    if tc_cfg is not None and getattr(tc_cfg, "enabled", False):
        detectors.append(
            TimeConsistencyDetector(TimeConsistencyConfig(**tc_cfg.model_dump()))
        )

    return detectors
