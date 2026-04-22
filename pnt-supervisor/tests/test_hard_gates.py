from types import SimpleNamespace

from pnt_supervisor.core.enums import FixType
from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.detectors.hard_gates import HardGatesDetector


def _cfg() -> SimpleNamespace:
    return SimpleNamespace(
        no_fix_timeout_s=5.0,
        stale_timeout_s=2.0,
        impossible_jump_m=150.0,
        frozen_solution_limit=5.0,
        extreme_hdop=10.0,
    )


def test_stale_epochs_trigger_hard_fail() -> None:
    detector = HardGatesDetector()
    obs = EpochObservation(t_sec=10.0, fix_valid=True, hdop=1.0, fix_type=FixType.FIX_3D)
    features = FeatureVector(values={"gap_s": 3.0})

    out = detector.evaluate(obs, features, _cfg())

    assert out.hard_fail is True
    assert "STALE_DATA_TIMEOUT" in out.reason_codes
    assert out.score == 1.0


def test_impossible_jump_triggers_hard_fail() -> None:
    detector = HardGatesDetector()
    obs = EpochObservation(t_sec=2.0, fix_valid=True, hdop=1.0, fix_type=FixType.FIX_3D)
    features = FeatureVector(values={"jump_distance_m": 500.0})

    out = detector.evaluate(obs, features, _cfg())

    assert out.hard_fail is True
    assert "IMPOSSIBLE_JUMP" in out.reason_codes
