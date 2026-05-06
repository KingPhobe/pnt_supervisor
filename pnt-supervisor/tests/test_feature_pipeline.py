from pnt_supervisor.core import FeatureFlag, FeatureValue
from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.core.platform import PlatformConfig
from pnt_supervisor.features import FeaturePipeline


def _obs(
    t: float,
    *,
    lat: float = 37.0,
    lon: float = -122.0,
    alt: float = 10.0,
    speed: float = 0.0,
    course: float = 0.0,
    climb: float = 0.0,
    fix_valid: bool = True,
    num_sats: int = 8,
    hdop: float = 1.0,
) -> EpochObservation:
    return EpochObservation(
        t_sec=t,
        lat_deg=lat,
        lon_deg=lon,
        alt_m=alt,
        speed_mps=speed,
        course_deg=course,
        climb_mps=climb,
        fix_valid=fix_valid,
        num_sats=num_sats,
        hdop=hdop,
    )


def test_default_pipeline_extract_returns_feature_vector_with_observation_timestamp() -> None:
    obs = _obs(12.5)

    out = FeaturePipeline.default().extract(obs)

    assert isinstance(out, FeatureVector)
    assert out.t_sec == obs.t_sec


def test_first_epoch_default_pipeline_includes_all_feature_groups() -> None:
    out = FeaturePipeline.default().extract(_obs(0.0))

    assert FeatureValue.GAP_S in out.values
    assert FeatureValue.FIX_VALID_NUMERIC in out.values
    assert FeatureValue.FD_SPEED_MPS in out.values
    assert FeatureValue.TIME_SINCE_LAST_INVALID in out.values
    assert FeatureFlag.TIMESTAMP_BACKWARDS in out.flags
    assert FeatureFlag.GEOMETRY_BAD in out.flags
    assert FeatureFlag.TRACK_GEOMETRY_AMBIGUOUS in out.flags
    assert FeatureFlag.REACQ_UNSTABLE in out.flags


def test_two_epoch_default_pipeline_produces_nonzero_second_epoch_kinematics() -> None:
    pipeline = FeaturePipeline.default()
    pipeline.extract(_obs(0.0, lat=37.0, lon=-122.0, speed=0.0))

    out = pipeline.extract(
        _obs(1.0, lat=37.000009, lon=-122.0, speed=1.0, climb=0.1, alt=10.1)
    )

    assert out.values[FeatureValue.JUMP_DISTANCE_M] > 0.0
    assert out.values[FeatureValue.FD_SPEED_MPS] > 0.0
    assert out.values[FeatureValue.CLIMB_MISMATCH_MPS] >= 0.0


def test_default_pipeline_quadcopter_platform_preserves_hover_behavior() -> None:
    pipeline = FeaturePipeline.default(platform_config=PlatformConfig.quadcopter())
    pipeline.extract(_obs(0.0, lat=37.0, lon=-122.0, speed=0.0))

    out = pipeline.extract(_obs(1.0, lat=37.0, lon=-122.0, speed=0.0, course=90.0))

    assert out.flags[FeatureFlag.TRACK_GEOMETRY_AMBIGUOUS] is True
    assert out.flags[FeatureFlag.HOVER_VALID] is True
    assert out.flags[FeatureFlag.LOW_MOTION_SUSPICIOUS] is False
