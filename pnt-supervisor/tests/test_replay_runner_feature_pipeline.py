from pathlib import Path

import pytest

from pnt_supervisor.adapters.base import ObservationAdapter
from pnt_supervisor.core.enums import FixType
from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.evaluation import ReplayRunner
from pnt_supervisor.features import FeatureExtractor, FeaturePipeline


class SyntheticAdapter(ObservationAdapter):
    def __init__(self, observations: list[EpochObservation]) -> None:
        self._observations = observations

    def reset(self) -> None:
        return None

    def iter_observations(self):
        yield from self._observations


class MarkerExtractor(FeatureExtractor):
    def extract(self, obs: EpochObservation, out: FeatureVector) -> FeatureVector:
        out = self._prepare_output(obs, out)
        out.values["marker_feature"] = obs.t_sec + 10.0
        self.context.append(obs)
        return out


def _adapter() -> SyntheticAdapter:
    return SyntheticAdapter(
        [
            EpochObservation(
                t_sec=0.0,
                source_name="synthetic",
                fix_valid=True,
                fix_type=FixType.FIX_3D,
                lat_deg=37.0,
                lon_deg=-122.0,
                alt_m=10.0,
                speed_mps=1.0,
                msg_gap_s=1.0,
                hdop=0.9,
                num_sats=10,
            ),
            EpochObservation(
                t_sec=1.0,
                source_name="synthetic",
                fix_valid=True,
                fix_type=FixType.FIX_3D,
                lat_deg=37.000009,
                lon_deg=-122.0,
                alt_m=10.1,
                speed_mps=1.0,
                msg_gap_s=1.0,
                hdop=0.9,
                num_sats=10,
            ),
        ]
    )


def test_replay_runner_uses_provided_feature_pipeline(tmp_path: Path) -> None:
    pipeline = FeaturePipeline([MarkerExtractor()])
    runner = ReplayRunner(_adapter(), feature_pipeline=pipeline)

    result = runner.run(tmp_path)

    assert runner.feature_pipeline is pipeline
    assert len(result.epoch_rows) == 2


def test_replay_runner_deprecated_feature_extractors_path(tmp_path: Path) -> None:
    runner = ReplayRunner(_adapter(), feature_extractors=[MarkerExtractor()])

    result = runner.run(tmp_path)

    assert isinstance(runner.feature_pipeline, FeaturePipeline)
    assert len(result.epoch_rows) == 2


def test_replay_runner_rejects_feature_pipeline_and_feature_extractors() -> None:
    with pytest.raises(ValueError, match="Pass either feature_pipeline or feature_extractors"):
        ReplayRunner(
            _adapter(),
            feature_pipeline=FeaturePipeline([MarkerExtractor()]),
            feature_extractors=[MarkerExtractor()],
        )


def test_default_replay_runner_pipeline_includes_time_consistency_extractor() -> None:
    runner = ReplayRunner(_adapter())

    assert any(
        extractor.__class__.__name__ == "TimeConsistencyFeatureExtractor"
        for extractor in runner.feature_pipeline.extractors
    )


def test_default_replay_runner_pipeline_starts_with_canonical_order() -> None:
    runner = ReplayRunner(_adapter())

    class_names = [
        extractor.__class__.__name__ for extractor in runner.feature_pipeline.extractors
    ]

    assert class_names[:4] == [
        "TimingFeatureExtractor",
        "QualityFeatureExtractor",
        "KinematicFeatureExtractor",
        "RecoveryFeatureExtractor",
    ]
    assert "TimeConsistencyFeatureExtractor" in class_names[4:]
