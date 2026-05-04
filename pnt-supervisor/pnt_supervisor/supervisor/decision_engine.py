from dataclasses import dataclass

from pnt_supervisor.core.enums import NavState
from pnt_supervisor.core.models import FeatureVector, SupervisorDecision


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
            "timestamp_backwards",
            "kinematic_time_invalid",
        ]

        degraded_flags = [
            "hdop_bad",
            "geometry_bad",
            "track_geometry_ambiguous",
            "low_motion_suspicious",
        ]

        for name in hard_invalid_flags:
            if flags.get(name, False):
                reasons.append(name)

        if reasons:
            return SupervisorDecision(nav_state=NavState.INVALID, nav_score=self.policy.invalid_score, reasons=reasons, hard_fail_active=True)

        if flags.get("reacq_unstable", False):
            return SupervisorDecision(nav_state=NavState.RECOVERING, nav_score=self.policy.recovering_score, reasons=["reacq_unstable"], hard_fail_active=False)

        for name in degraded_flags:
            if flags.get(name, False):
                reasons.append(name)

        if values.get("stale_count", 0.0) > self.policy.max_stale_count:
            reasons.append("stale_count")

        if values.get("state_flap_count", 0.0) > self.policy.max_state_flap_count:
            reasons.append("state_flap_count")

        if reasons:
            return SupervisorDecision(nav_state=NavState.DEGRADED, nav_score=self.policy.degraded_score, reasons=reasons, hard_fail_active=False)

        return SupervisorDecision(nav_state=NavState.GOOD, nav_score=self.policy.good_score, reasons=[], hard_fail_active=False)
