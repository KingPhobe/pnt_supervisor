"""Soft stale-data detector."""

from __future__ import annotations

from typing import Any

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector

from .base import Detector, clamp01


class StaleDataDetector(Detector):
    name = "stale_data"

    def evaluate(self, obs: EpochObservation, features: FeatureVector, config: Any) -> DetectorResult:
        gap_ratio = clamp01(float(features.values.get("gap_ratio", 0.0)) / 3.0)
        stale_count = clamp01(float(features.values.get("stale_count", 0.0)) / 3.0)
        backwards = 1.0 if bool(features.flags.get("timestamp_backwards", False)) else 0.0
        frozen = clamp01(float(features.values.get("frozen_solution_count", 0.0)) / 5.0)

        score = clamp01(0.35 * gap_ratio + 0.25 * stale_count + 0.20 * backwards + 0.20 * frozen)

        reason_codes: list[str] = []
        if backwards:
            reason_codes.append("TIMESTAMP_BACKWARDS")
        if stale_count >= 0.67:
            reason_codes.append("REPEATED_STALE_EPOCHS")
        if frozen >= 0.8:
            reason_codes.append("FROZEN_TRACK")

        return DetectorResult(
            detector_name=self.name,
            score=score,
            hard_fail=False,
            reason_codes=reason_codes,
            metrics={
                "gap_ratio_norm": gap_ratio,
                "stale_count_norm": stale_count,
                "timestamp_backwards": backwards,
                "frozen_solution_norm": frozen,
            },
        )
