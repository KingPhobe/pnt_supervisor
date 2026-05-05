from dataclasses import dataclass

from pnt_supervisor.core import FeatureFlag, FeatureValue, FeatureVector, NavState, SupervisorDecision


@dataclass(slots=True)
class DecisionPolicy:
    max_state_flap_count: float = 3.0
    max_stale_count: float = 2.0
    degraded_score: float = 0.5
    invalid_score: float = 0.0
    good_score: float = 1.0
    recovering_score: float = 0.6


class DecisionEngine:
    def __init__(self, policy: DecisionPolicy | None = None) -> None:
        self.policy = policy or DecisionPolicy()

    def decide(self, features: FeatureVector) -> SupervisorDecision:
        reasons: list[str] = []
        flags = features.flags
        values = features.values

        hard_invalid_flags = [
            FeatureFlag.TIMESTAMP_BACKWARDS,
            FeatureFlag.KINEMATIC_TIME_INVALID,
        ]

        degraded_flags = [
            FeatureFlag.HDOP_BAD,
            FeatureFlag.GEOMETRY_BAD,
            FeatureFlag.LOW_MOTION_SUSPICIOUS,
        ]

        for name in hard_invalid_flags:
            if flags.get(name, False):
                reasons.append(name)

        if reasons:
            return SupervisorDecision(nav_state=NavState.INVALID, nav_score=self.policy.invalid_score, reasons=reasons, hard_fail_active=True)

        if flags.get(FeatureFlag.REACQ_UNSTABLE, False):
            return SupervisorDecision(nav_state=NavState.RECOVERING, nav_score=self.policy.recovering_score, reasons=[FeatureFlag.REACQ_UNSTABLE], hard_fail_active=False)

        for name in degraded_flags:
            if flags.get(name, False):
                reasons.append(name)

        if flags.get(FeatureFlag.TRACK_GEOMETRY_AMBIGUOUS, False) and not flags.get(FeatureFlag.HOVER_VALID, False):
            reasons.append(FeatureFlag.TRACK_GEOMETRY_AMBIGUOUS)

        if values.get(FeatureValue.STALE_COUNT, 0.0) > self.policy.max_stale_count:
            reasons.append(FeatureValue.STALE_COUNT)

        if values.get(FeatureValue.STATE_FLAP_COUNT, 0.0) > self.policy.max_state_flap_count:
            reasons.append(FeatureValue.STATE_FLAP_COUNT)

        if reasons:
            return SupervisorDecision(nav_state=NavState.DEGRADED, nav_score=self.policy.degraded_score, reasons=reasons, hard_fail_active=False)

        return SupervisorDecision(nav_state=NavState.GOOD, nav_score=self.policy.good_score, reasons=[], hard_fail_active=False)
