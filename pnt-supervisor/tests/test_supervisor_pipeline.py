from pnt_supervisor.core import NavState, PlatformConfig
from pnt_supervisor.core.models import EpochObservation, FeatureVector, SupervisorDecision
from pnt_supervisor.features import FeaturePipeline
from pnt_supervisor.supervisor import SupervisorPipeline, SupervisorStepResult


def _obs(
    t: float,
    *,
    lat: float = 37.0,
    lon: float = -122.0,
    alt: float = 10.0,
    speed: float = 1.0,
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


def test_default_supervisor_pipeline_returns_step_result() -> None:
    obs = _obs(0.0)

    result = SupervisorPipeline().step(obs)

    assert isinstance(result, SupervisorStepResult)
    assert result.observation is obs
    assert isinstance(result.features, FeatureVector)
    assert isinstance(result.decision, SupervisorDecision)


def test_default_supervisor_pipeline_first_valid_observation_is_good() -> None:
    result = SupervisorPipeline().step(_obs(0.0))

    assert result.decision.nav_state == NavState.GOOD
    assert result.decision.reasons == []


def test_timestamp_backwards_sequence_is_invalid_on_second_step() -> None:
    supervisor = SupervisorPipeline()
    supervisor.step(_obs(10.0))

    result = supervisor.step(_obs(9.0))

    assert result.decision.nav_state == NavState.INVALID
    assert result.decision.hard_fail_active is True


def test_quadcopter_hover_sequence_stays_good_for_hover_epoch() -> None:
    feature_pipeline = FeaturePipeline.default(platform_config=PlatformConfig.quadcopter())
    supervisor = SupervisorPipeline(feature_pipeline=feature_pipeline)
    supervisor.step(_obs(0.0, lat=37.0, lon=-122.0, speed=0.0))

    result = supervisor.step(_obs(1.0, lat=37.0, lon=-122.0, speed=0.0, course=90.0))

    assert result.decision.nav_state == NavState.GOOD
    assert result.decision.reasons == []
