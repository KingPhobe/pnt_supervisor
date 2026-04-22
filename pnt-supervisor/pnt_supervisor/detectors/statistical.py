"""Simple deterministic EWMA/CUSUM-style statistical detector."""

from __future__ import annotations

from typing import Any

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector

from .base import Detector, clamp01


class StatisticalDetector(Detector):
    name = "statistical"

    def __init__(self, alpha: float = 0.25) -> None:
        self.alpha = alpha
        self.ewma_jump = 0.0
        self.ewma_speed = 0.0
        self.ewma_hdop = 0.0
        self.cusum = 0.0

    def _get(self, config: Any, key: str, default: float) -> float:
        if hasattr(config, "thresholds") and hasattr(config.thresholds, key):
            return float(getattr(config.thresholds, key))
        if hasattr(config, "vehicle") and hasattr(config.vehicle, key):
            return float(getattr(config.vehicle, key))
        if hasattr(config, key):
            return float(getattr(config, key))
        return default

    def evaluate(self, obs: EpochObservation, features: FeatureVector, config: Any) -> DetectorResult:
        jump = float(features.values.get("jump_distance_m", 0.0))
        speed = float(features.values.get("speed_mismatch_mps", 0.0))
        hdop = float(features.values.get("hdop", obs.hdop))

        self.ewma_jump = self.alpha * jump + (1.0 - self.alpha) * self.ewma_jump
        self.ewma_speed = self.alpha * speed + (1.0 - self.alpha) * self.ewma_speed
        self.ewma_hdop = self.alpha * hdop + (1.0 - self.alpha) * self.ewma_hdop

        jump_limit = self._get(config, "impossible_jump_m", 150.0)
        speed_limit = self._get(config, "max_speed_mps", 25.0)
        hdop_limit = self._get(config, "max_hdop", 2.5)

        jump_n = clamp01(self.ewma_jump / max(jump_limit, 1e-6))
        speed_n = clamp01(self.ewma_speed / max(speed_limit, 1e-6))
        hdop_n = clamp01(self.ewma_hdop / max(hdop_limit, 1e-6))

        innovation = max(0.0, 0.5 * jump_n + 0.3 * speed_n + 0.2 * hdop_n - 0.1)
        self.cusum = clamp01(0.85 * self.cusum + innovation)

        score = clamp01(0.6 * self.cusum + 0.4 * (0.5 * jump_n + 0.3 * speed_n + 0.2 * hdop_n))

        reason_codes: list[str] = []
        if self.cusum >= 0.7:
            reason_codes.append("PERSISTENT_STATISTICAL_DRIFT")

        return DetectorResult(
            detector_name=self.name,
            score=score,
            hard_fail=False,
            reason_codes=reason_codes,
            metrics={
                "ewma_jump": self.ewma_jump,
                "ewma_speed": self.ewma_speed,
                "ewma_hdop": self.ewma_hdop,
                "cusum": self.cusum,
            },
        )
