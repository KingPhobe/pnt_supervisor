from pathlib import Path
from typing import Any

from pnt_supervisor.adapters.base import ObservationAdapter
from pnt_supervisor.core.enums import FixType
from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector
from pnt_supervisor.evaluation import ReplayRunner
from pnt_supervisor.evaluation.protocols import DetectorLike


class SyntheticAdapter(ObservationAdapter):
    def __init__(self, observations: list[EpochObservation]) -> None:
        self._observations = observations

    def reset(self) -> None:
        return None

    def iter_observations(self):
        yield from self._observations


class FakeDetector:
    detector_name = "fake_detector"

    def evaluate(
        self,
        obs: EpochObservation,
        features: FeatureVector,
        config: Any | None = None,
    ) -> DetectorResult:
        return DetectorResult(detector_name=self.detector_name, score=0.0)


def test_detector_like_imports() -> None:
    assert DetectorLike is not None


def test_detector_like_fake_detector_works_with_replay_runner(tmp_path: Path) -> None:
    fake_detector = FakeDetector()
    obs = [
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
        )
    ]

    runner = ReplayRunner(SyntheticAdapter(obs), detectors=(fake_detector,))
    result = runner.run(tmp_path)

    assert runner.detectors == [fake_detector]
    assert result.summary["total_epochs"] == 1
