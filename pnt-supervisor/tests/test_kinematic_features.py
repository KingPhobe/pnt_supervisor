from pnt_supervisor.core.platform import PlatformConfig
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


def test_kinematics_negative_dt_sets_time_invalid_without_huge_rates() -> None:
    extractor = KinematicFeatureExtractor()
    extractor.extract(EpochObservation(t_sec=5.0, lat_deg=37.0, lon_deg=-122.0), FeatureVector())

    out = extractor.extract(
        EpochObservation(t_sec=4.0, lat_deg=38.0, lon_deg=-122.0, speed_mps=0.0),
        FeatureVector(),
    )

    assert out.flags["kinematic_time_invalid"] is True
    assert out.flags["track_geometry_ambiguous"] is True
    assert out.values["fd_speed_mps"] == 0.0
    assert out.values["turn_rate_degps"] == 0.0


def test_fixed_wing_low_motion_is_suspicious_and_does_not_compute_bearing() -> None:
    extractor = KinematicFeatureExtractor(platform_config=PlatformConfig.fixed_wing())
    extractor.extract(EpochObservation(t_sec=0.0, lat_deg=37.0, lon_deg=-122.0, speed_mps=0.0), FeatureVector())

    out = extractor.extract(
        EpochObservation(t_sec=1.0, lat_deg=37.0, lon_deg=-122.0, speed_mps=0.0, course_deg=90.0),
        FeatureVector(),
    )

    assert out.flags["track_geometry_ambiguous"] is True
    assert out.flags["hover_valid"] is False
    assert out.flags["low_motion_suspicious"] is True
    assert out.values["course_track_mismatch_deg"] == 0.0


def test_quadcopter_hover_does_not_create_low_motion_suspicion() -> None:
    extractor = KinematicFeatureExtractor(platform_config=PlatformConfig.quadcopter())
    extractor.extract(EpochObservation(t_sec=0.0, lat_deg=37.0, lon_deg=-122.0, speed_mps=0.0), FeatureVector())

    out = extractor.extract(
        EpochObservation(t_sec=1.0, lat_deg=37.0, lon_deg=-122.0, speed_mps=0.0, course_deg=90.0),
        FeatureVector(),
    )

    assert out.flags["track_geometry_ambiguous"] is True
    assert out.flags["hover_valid"] is True
    assert out.flags["low_motion_suspicious"] is False
    assert out.values["course_track_mismatch_deg"] == 0.0
