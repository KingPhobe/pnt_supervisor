from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.features.time_consistency import TimeConsistencyFeatureExtractor


def _obs(t: float, gps_t: float, lat: float = 37.0, speed: float = 5.0) -> EpochObservation:
    return EpochObservation(t_sec=t, lat_deg=lat, lon_deg=-122.0, alt_m=10.0, speed_mps=speed, extras={"gps_time_s": gps_t})


def test_constant_1hz_timestamps_low_mismatch() -> None:
    ex = TimeConsistencyFeatureExtractor(window_s=10.0, min_samples=5)
    out = FeatureVector()
    for i in range(7):
        out = ex.extract(_obs(float(i), float(i)), FeatureVector())
    assert out.values["time_dt_mismatch_s"] == 0.0
    assert abs(out.values["time_clock_drift_ppm"]) < 1.0


def test_time_drift_reports_high_clock_drift_ppm() -> None:
    ex = TimeConsistencyFeatureExtractor(window_s=20.0, min_samples=5)
    out = FeatureVector()
    for i in range(10):
        out = ex.extract(_obs(float(i), 1.001 * float(i)), FeatureVector())
    assert out.flags["time_fit_available"] is True
    assert out.values["time_clock_drift_ppm"] > 900.0


def test_motion_time_mismatch_feature_high() -> None:
    ex = TimeConsistencyFeatureExtractor()
    ex.extract(_obs(0.0, 0.0, lat=37.0, speed=5.0), FeatureVector())
    out = ex.extract(_obs(1.0, 1.0, lat=37.0009, speed=5.0), FeatureVector())
    assert out.values["time_motion_residual_m"] > 50.0
