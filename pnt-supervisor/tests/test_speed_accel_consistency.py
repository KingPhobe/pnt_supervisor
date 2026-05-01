from __future__ import annotations

from pnt_supervisor.core.config import AppConfig
from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.detectors.speed_accel_consistency import (
    SpeedAccelConsistencyConfig,
    SpeedAccelConsistencyDetector,
)


def _obs(t: float, speed: float, ax: float | None, ay: float | None, az: float | None) -> EpochObservation:
    extras: dict[str, float] = {}
    if ax is not None:
        extras["IMU_AccX"] = ax
    if ay is not None:
        extras["IMU_AccY"] = ay
    if az is not None:
        extras["IMU_AccZ"] = az
    extras["timestamp"] = t
    extras["GPS_0_Spd"] = speed
    return EpochObservation(t_sec=t, speed_mps=speed, extras=extras)


def test_constant_speed_quiet_imu_has_no_anomaly() -> None:
    detector = SpeedAccelConsistencyDetector(SpeedAccelConsistencyConfig(min_samples=5, consecutive_windows_to_flag=3))

    out = None
    for i in range(10):
        out = detector.evaluate(_obs(float(i), 10.0, 0.0, 0.0, 9.80665), FeatureVector(), AppConfig())

    assert out is not None
    assert out.metrics["fault_flag"] == 0.0
    assert out.metrics["warning_flag"] == 0.0
    assert out.reason_codes == ["GPS_IMU_ACCEL_CONSISTENT"]


def test_speed_ramp_matching_imu_has_no_anomaly() -> None:
    detector = SpeedAccelConsistencyDetector(SpeedAccelConsistencyConfig(min_samples=5, consecutive_windows_to_flag=2))

    out = None
    for i in range(12):
        speed = 2.0 + 0.5 * i
        out = detector.evaluate(_obs(float(i), speed, 0.0, 0.0, 9.80665 + 0.5), FeatureVector(), AppConfig())

    assert out is not None
    assert out.metrics["fault_flag"] == 0.0
    assert out.metrics["warning_flag"] == 0.0
    assert out.metrics["health_score"] > 0.8


def test_speed_jumps_with_quiet_imu_flags_anomaly() -> None:
    detector = SpeedAccelConsistencyDetector(
        SpeedAccelConsistencyConfig(min_samples=5, consecutive_windows_to_flag=2, warning_residual_mps2=1.0, fault_residual_mps2=2.0)
    )

    speeds = [0.0, 0.0, 0.0, 8.0, 16.0, 24.0, 32.0, 40.0]
    out = None
    for i, speed in enumerate(speeds):
        out = detector.evaluate(_obs(float(i), speed, 0.0, 0.0, 9.80665), FeatureVector(), AppConfig())

    assert out is not None
    assert out.metrics["fault_flag"] == 1.0
    assert "FAULT" in out.reason_codes[0]


def test_missing_accel_samples_yields_no_decision() -> None:
    detector = SpeedAccelConsistencyDetector(SpeedAccelConsistencyConfig(min_samples=4))

    out = None
    for i in range(6):
        out = detector.evaluate(_obs(float(i), 5.0, None, None, None), FeatureVector(), AppConfig())

    assert out is not None
    assert out.metrics["decision_available"] == 0.0
    assert out.reason_codes == ["NO_DECISION_INSUFFICIENT_VALID_SAMPLES"]


def test_irregular_timestamps_still_estimate_derivative() -> None:
    detector = SpeedAccelConsistencyDetector(SpeedAccelConsistencyConfig(min_samples=5, consecutive_windows_to_flag=2))

    timestamps = [0.0, 0.7, 1.9, 2.2, 3.8, 5.1, 6.0]
    out = None
    for t in timestamps:
        speed = 3.0 + 2.0 * t
        out = detector.evaluate(_obs(t, speed, 0.0, 0.0, 9.80665 + 2.0), FeatureVector(), AppConfig())

    assert out is not None
    assert abs(out.metrics["gps_accel_mps2"] - 2.0) < 0.1
    assert out.metrics["warning_flag"] == 0.0
