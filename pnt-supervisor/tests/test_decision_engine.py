from pnt_supervisor.core.enums import NavState
from pnt_supervisor.core.models import FeatureVector
from pnt_supervisor.supervisor import DecisionEngine


def test_default_feature_vector_gives_good() -> None:
    decision = DecisionEngine().decide(FeatureVector())
    assert decision.nav_state == NavState.GOOD


def test_timestamp_backwards_gives_invalid_hard_fail() -> None:
    decision = DecisionEngine().decide(FeatureVector(flags={"timestamp_backwards": True}))
    assert decision.nav_state == NavState.INVALID
    assert decision.hard_fail_active is True


def test_kinematic_time_invalid_gives_invalid() -> None:
    decision = DecisionEngine().decide(FeatureVector(flags={"kinematic_time_invalid": True}))
    assert decision.nav_state == NavState.INVALID


def test_reacq_unstable_gives_recovering() -> None:
    decision = DecisionEngine().decide(FeatureVector(flags={"reacq_unstable": True}))
    assert decision.nav_state == NavState.RECOVERING


def test_geometry_bad_gives_degraded() -> None:
    decision = DecisionEngine().decide(FeatureVector(flags={"geometry_bad": True}))
    assert decision.nav_state == NavState.DEGRADED


def test_low_motion_suspicious_gives_degraded() -> None:
    decision = DecisionEngine().decide(FeatureVector(flags={"low_motion_suspicious": True}))
    assert decision.nav_state == NavState.DEGRADED


def test_hover_valid_alone_stays_good() -> None:
    decision = DecisionEngine().decide(FeatureVector(flags={"hover_valid": True}))
    assert decision.nav_state == NavState.GOOD


def test_stale_count_above_threshold_gives_degraded() -> None:
    decision = DecisionEngine().decide(FeatureVector(values={"stale_count": 3.0}))
    assert decision.nav_state == NavState.DEGRADED


def test_state_flap_count_above_threshold_gives_degraded() -> None:
    decision = DecisionEngine().decide(FeatureVector(values={"state_flap_count": 4.0}))
    assert decision.nav_state == NavState.DEGRADED
