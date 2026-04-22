"""Soft kinematic anomaly detector."""

from __future__ import annotations

from typing import Any

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector

from .base import Detector, clamp01


class KinematicAnomalyDetector(Detector):
    name = "kinematic_anomaly"

    def _get(self, config: Any, key: str, default: float) -> float:
        if hasattr(config, "thresholds") and hasattr(config.thresholds, key):
            return float(getattr(config.thresholds, key))
        if hasattr(config, "vehicle") and hasattr(config.vehicle, key):
            return float(getattr(config.vehicle, key))
        if hasattr(config, key):
            return float(getattr(config, key))
        return default

    def evaluate(self, obs: EpochObservation, features: FeatureVector, config: Any) -> DetectorResult:
        jump_limit = self._get(config, "impossible_jump_m", 150.0)
        speed_limit = self._get(config, "max_speed_mps", 25.0)
        course_limit = self._get(config, "max_turn_rate_dps", 120.0)
        climb_limit = self._get(config, "max_climb_mps", 8.0)

        jump_n = clamp01(float(features.values.get("jump_distance_m", 0.0)) / max(jump_limit, 1e-6))
        speed_n = clamp01(float(features.values.get("speed_mismatch_mps", 0.0)) / max(speed_limit, 1e-6))
        course_n = clamp01(float(features.values.get("course_track_mismatch_deg", 0.0)) / max(course_limit, 1e-6))
        climb_n = clamp01(float(features.values.get("climb_mismatch_mps", 0.0)) / max(climb_limit, 1e-6))

        weighted = 0.35 * jump_n + 0.30 * speed_n + 0.20 * course_n + 0.15 * climb_n
        score = clamp01(weighted)

        reason_codes: list[str] = []
        if jump_n >= 0.8:
            reason_codes.append("HIGH_JUMP_DISTANCE")
        if speed_n >= 0.8:
            reason_codes.append("HIGH_SPEED_MISMATCH")
        if course_n >= 0.8:
            reason_codes.append("HIGH_COURSE_MISMATCH")
        if climb_n >= 0.8:
            reason_codes.append("HIGH_CLIMB_MISMATCH")

        return DetectorResult(
            detector_name=self.name,
            score=score,
            hard_fail=False,
            reason_codes=reason_codes,
            metrics={
                "jump_norm": jump_n,
                "speed_norm": speed_n,
                "course_norm": course_n,
                "climb_norm": climb_n,
            },
        )
