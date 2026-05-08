from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pnt_supervisor.detectors import (
    HardGatesDetector,
    KinematicAnomalyDetector,
    ModeFlapDetector,
    SpeedAccelConsistencyDetector,
    StaleDataDetector,
    StatisticalDetector,
    TimeConsistencyDetector,
)
from pnt_supervisor.evaluation.replay_pipeline_factory import (
    build_default_detectors,
    build_default_feature_pipeline,
)
from pnt_supervisor.features import TimeConsistencyFeatureExtractor


@dataclass(slots=True)
class FakeDetectorConfig:
    enabled: bool

    def model_dump(self) -> dict[str, Any]:
        return {"enabled": self.enabled}


@dataclass(slots=True)
class FakeConfig:
    time_consistency: FakeDetectorConfig | None = None
    speed_accel_consistency: FakeDetectorConfig | None = None


def test_build_default_feature_pipeline_starts_with_canonical_order_and_time_consistency() -> None:
    pipeline = build_default_feature_pipeline()

    class_names = [extractor.__class__.__name__ for extractor in pipeline.extractors]

    assert class_names[:4] == [
        "TimingFeatureExtractor",
        "QualityFeatureExtractor",
        "KinematicFeatureExtractor",
        "RecoveryFeatureExtractor",
    ]
    assert any(
        isinstance(extractor, TimeConsistencyFeatureExtractor)
        for extractor in pipeline.extractors
    )


def test_build_default_detectors_includes_baseline_detectors() -> None:
    detectors = build_default_detectors(None)

    detector_types = {detector.__class__ for detector in detectors}

    assert HardGatesDetector in detector_types
    assert KinematicAnomalyDetector in detector_types
    assert StaleDataDetector in detector_types
    assert ModeFlapDetector in detector_types
    assert StatisticalDetector in detector_types


def test_build_default_detectors_adds_time_consistency_when_enabled() -> None:
    config = FakeConfig(time_consistency=FakeDetectorConfig(enabled=True))

    detectors = build_default_detectors(config)

    assert any(isinstance(detector, TimeConsistencyDetector) for detector in detectors)


def test_build_default_detectors_adds_speed_accel_consistency_when_enabled() -> None:
    config = FakeConfig(speed_accel_consistency=FakeDetectorConfig(enabled=True))

    detectors = build_default_detectors(config)

    assert any(isinstance(detector, SpeedAccelConsistencyDetector) for detector in detectors)
