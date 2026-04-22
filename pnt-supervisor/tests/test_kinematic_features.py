from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.features.kinematics import KinematicFeatureExtractor


def test_large_jump_creates_large_jump_distance() -> None:
    extractor = KinematicFeatureExtractor()
    extractor.extract(EpochObservation(t_sec=0.0, lat_deg=37.0, lon_deg=-122.0), FeatureVector())

    out = extractor.extract(EpochObservation(t_sec=1.0, lat_deg=38.0, lon_deg=-122.0), FeatureVector())

    assert out.values["jump_distance_m"] > 100000.0


def test_stable_replay_has_low_speed_mismatch() -> None:
    extractor = KinematicFeatureExtractor()
    extractor.extract(EpochObservation(t_sec=0.0, lat_deg=37.0, lon_deg=-122.0, speed_mps=0.0), FeatureVector())

    out = extractor.extract(
        EpochObservation(t_sec=1.0, lat_deg=37.000009, lon_deg=-122.0, speed_mps=1.0),
        FeatureVector(),
    )

    assert out.values["speed_mismatch_mps"] < 0.5
