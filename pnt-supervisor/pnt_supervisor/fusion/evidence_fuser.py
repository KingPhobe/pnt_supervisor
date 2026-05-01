"""Evidence fusion utilities for combining detector outputs into nav trust."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pnt_supervisor.core.models import DetectorResult

DEFAULT_DETECTOR_WEIGHTS: dict[str, float] = {
    "stale_data": 0.20,
    "kinematic_anomaly": 0.25,
    "mode_flap": 0.15,
    "statistical": 0.20,
    "speed_accel_consistency": 0.20,
}


@dataclass(slots=True)
class FusedEvidence:
    """Normalized fused evidence summary used by decision-state logic."""

    nav_score: float
    reasons: list[str] = field(default_factory=list)
    hard_fail_active: bool = False

    def __post_init__(self) -> None:
        self.nav_score = min(1.0, max(0.0, self.nav_score))


class EvidenceFuser:
    """Combine detector outputs into a single [0, 1] navigation-health score."""

    def __init__(self, config: Any | None = None) -> None:
        self._config = config

    def _weights_from_config(self) -> dict[str, float]:
        fusion_cfg = getattr(self._config, "fusion", self._config)
        configured = getattr(fusion_cfg, "detector_weights", None)
        if isinstance(configured, dict):
            return {k: max(0.0, float(v)) for k, v in configured.items()}
        return DEFAULT_DETECTOR_WEIGHTS.copy()

    def fuse(self, results: list[DetectorResult]) -> FusedEvidence:
        """Fuse detector results into health score, merged reasons, and hard-fail flag."""

        weights = self._weights_from_config()
        weighted_health = 0.0
        total_weight = 0.0
        hard_fail_active = False
        reasons: list[str] = []

        for result in results:
            hard_fail_active = hard_fail_active or bool(result.hard_fail)

            for reason in result.reason_codes:
                if reason not in reasons:
                    reasons.append(reason)

            detector_weight = weights.get(result.detector_name, 0.0)
            if detector_weight <= 0.0:
                continue

            anomaly_score = min(1.0, max(0.0, float(result.score)))
            detector_health = 1.0 - anomaly_score
            weighted_health += detector_health * detector_weight
            total_weight += detector_weight

        nav_score = 1.0 if total_weight <= 0.0 else weighted_health / total_weight
        if hard_fail_active:
            nav_score = 0.0

        return FusedEvidence(nav_score=nav_score, reasons=reasons, hard_fail_active=hard_fail_active)
