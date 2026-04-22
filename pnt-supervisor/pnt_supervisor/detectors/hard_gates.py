"""Hard-fail detector for immediate integrity violations."""

from __future__ import annotations

from typing import Any

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector

from .base import Detector


class HardGatesDetector(Detector):
    name = "hard_gates"

    def _get(self, config: Any, key: str, default: float) -> float:
        if hasattr(config, "thresholds") and hasattr(config.thresholds, key):
            return float(getattr(config.thresholds, key))
        if hasattr(config, key):
            return float(getattr(config, key))
        return default

    def evaluate(self, obs: EpochObservation, features: FeatureVector, config: Any) -> DetectorResult:
        no_fix_timeout_s = self._get(config, "no_fix_timeout_s", 5.0)
        stale_timeout_s = self._get(config, "stale_timeout_s", 2.0)
        impossible_jump_m = self._get(config, "impossible_jump_m", 150.0)
        frozen_solution_limit = self._get(config, "frozen_solution_limit", 5.0)
        extreme_hdop = self._get(config, "extreme_hdop", 10.0)

        reason_codes: list[str] = []
        metrics = {
            "time_since_valid_fix_s": float(features.values.get("time_since_last_valid_fix_s", 0.0)),
            "gap_s": float(features.values.get("gap_s", 0.0)),
            "jump_distance_m": float(features.values.get("jump_distance_m", 0.0)),
            "frozen_solution_count": float(features.values.get("frozen_solution_count", 0.0)),
            "hdop": float(features.values.get("hdop", obs.hdop)),
        }

        if not obs.fix_valid and metrics["time_since_valid_fix_s"] >= no_fix_timeout_s:
            reason_codes.append("NO_VALID_FIX_TIMEOUT")
        if metrics["gap_s"] >= stale_timeout_s:
            reason_codes.append("STALE_DATA_TIMEOUT")
        if metrics["jump_distance_m"] >= impossible_jump_m:
            reason_codes.append("IMPOSSIBLE_JUMP")
        if metrics["frozen_solution_count"] >= frozen_solution_limit:
            reason_codes.append("FROZEN_SOLUTION")
        if metrics["hdop"] >= extreme_hdop:
            reason_codes.append("EXTREME_HDOP")

        hard_fail = len(reason_codes) > 0
        return DetectorResult(
            detector_name=self.name,
            score=1.0 if hard_fail else 0.0,
            hard_fail=hard_fail,
            reason_codes=reason_codes,
            metrics=metrics,
        )
