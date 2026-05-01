from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector
from pnt_supervisor.detectors.time_consistency import TimeConsistencyDetector


def _obs(t: float = 0.0, speed: float = 5.0) -> EpochObservation:
    return EpochObservation(t_sec=t, speed_mps=speed)


def test_constant_1hz_low_score_no_hard_fail() -> None:
    det = TimeConsistencyDetector()
    feat = FeatureVector(values={"time_dt_mismatch_s": 0.0, "time_dt_gps_s": 1.0})
    out = det.evaluate(_obs(), feat, None)
    assert out.score < 0.2
    assert out.hard_fail is False


def test_gps_time_freeze_persistence_triggers_fault() -> None:
    det = TimeConsistencyDetector()
    result: DetectorResult | None = None
    for i in range(3):
        feat = FeatureVector(values={"time_dt_mismatch_s": 1.0, "time_dt_gps_s": 0.0, "time_clock_drift_ppm": 500.0, "time_clock_fit_rms_s": 1.0, "time_motion_residual_m": 50.0, "time_implied_residual_s": 5.0}, flags={"time_gps_time_frozen": True, "time_fit_available": True})
        result = det.evaluate(_obs(float(i)), feat, None)
    assert result is not None
    assert result.hard_fail is True


def test_gps_time_backwards_immediate_hard_fail() -> None:
    det = TimeConsistencyDetector()
    feat = FeatureVector(values={"time_dt_gps_s": -1.0}, flags={"time_gps_time_backwards": True})
    out = det.evaluate(_obs(), feat, None)
    assert out.hard_fail is True


def test_stationary_motion_check_ignored() -> None:
    det = TimeConsistencyDetector()
    feat = FeatureVector(values={"time_motion_residual_m": 100.0, "time_implied_residual_s": 10.0})
    out = det.evaluate(_obs(speed=0.1), feat, None)
    assert out.score < 0.5
