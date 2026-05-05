from pnt_supervisor.core import FeatureFlag, FeatureValue, FeatureVector, NavState
from pnt_supervisor.supervisor import DecisionEngine, DecisionPolicy


def test_custom_policy_without_degraded_flags_does_not_degrade_geometry_bad() -> None:
    policy = DecisionPolicy(degraded_flags=())

    decision = DecisionEngine(policy).decide(
        FeatureVector(flags={FeatureFlag.GEOMETRY_BAD: True})
    )

    assert decision.nav_state == NavState.GOOD
    assert decision.reasons == []


def test_custom_policy_without_hard_invalid_flags_does_not_invalidate_timestamp_backwards() -> None:
    policy = DecisionPolicy(hard_invalid_flags=())

    decision = DecisionEngine(policy).decide(
        FeatureVector(flags={FeatureFlag.TIMESTAMP_BACKWARDS: True})
    )

    assert decision.nav_state == NavState.GOOD
    assert decision.hard_fail_active is False
    assert decision.reasons == []


def test_policy_can_disable_hover_exemption_for_track_geometry_ambiguity() -> None:
    policy = DecisionPolicy(hover_exempts_track_ambiguity=False)

    decision = DecisionEngine(policy).decide(
        FeatureVector(
            flags={
                FeatureFlag.TRACK_GEOMETRY_AMBIGUOUS: True,
                FeatureFlag.HOVER_VALID: True,
                FeatureFlag.LOW_MOTION_SUSPICIOUS: False,
            }
        )
    )

    assert decision.nav_state == NavState.DEGRADED
    assert FeatureFlag.TRACK_GEOMETRY_AMBIGUOUS in decision.reasons


def test_policy_max_stale_count_can_keep_stale_count_good() -> None:
    policy = DecisionPolicy(max_stale_count=10)

    decision = DecisionEngine(policy).decide(
        FeatureVector(values={FeatureValue.STALE_COUNT: 3.0})
    )

    assert decision.nav_state == NavState.GOOD
    assert decision.reasons == []
