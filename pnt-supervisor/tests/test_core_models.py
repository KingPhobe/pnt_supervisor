from pnt_supervisor.core.config import AppConfig, FusionConfig, ThresholdConfig, VehicleProfileConfig
from pnt_supervisor.core.enums import FixType, NavState, SourceType
from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector, SupervisorDecision


def test_enums_are_stable_strings() -> None:
    assert NavState.GOOD.value == "good"
    assert NavState.DEGRADED.value == "degraded"
    assert NavState.INVALID.value == "invalid"
    assert SourceType.NMEA_REPLAY.value == "nmea_replay"
    assert FixType.RTK_FIXED.value == "rtk_fixed"


def test_epoch_observation_defaults_construct() -> None:
    obs = EpochObservation()
    assert obs.fix_type == FixType.UNKNOWN
    assert obs.fix_valid is False
    assert obs.extras == {}


def test_feature_vector_defaults_construct() -> None:
    fv = FeatureVector()
    assert fv.values == {}
    assert fv.flags == {}
    assert fv.metadata == {}


def test_detector_result_defaults_construct() -> None:
    result = DetectorResult()
    assert result.detector_name == "unknown"
    assert result.hard_fail is False
    assert result.metrics == {}


def test_supervisor_decision_score_clamps() -> None:
    low = SupervisorDecision(nav_score=-0.1)
    high = SupervisorDecision(nav_score=1.2)
    ok = SupervisorDecision(nav_score=0.7)

    assert low.nav_score == 0.0
    assert high.nav_score == 1.0
    assert ok.nav_score == 0.7


def test_supervisor_decision_defaults_construct() -> None:
    decision = SupervisorDecision()
    assert decision.nav_state == NavState.UNKNOWN
    assert decision.hard_fail_active is False


def test_config_defaults_for_multirotor_profile() -> None:
    app = AppConfig()
    assert isinstance(app.vehicle, VehicleProfileConfig)
    assert isinstance(app.thresholds, ThresholdConfig)
    assert isinstance(app.fusion, FusionConfig)
    assert app.vehicle.name == "multirotor"
    assert app.vehicle.max_speed_mps > 0.0
