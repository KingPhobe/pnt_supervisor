"""Soft detector for mode/validity flapping behavior."""

from __future__ import annotations

from collections import deque
from typing import Any

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector

from .base import Detector, clamp01


class ModeFlapDetector(Detector):
    name = "mode_flap"

    def __init__(self, window: int = 20) -> None:
        self.valid_history: deque[bool] = deque(maxlen=window)
        self.fix_type_history: deque[str] = deque(maxlen=window)

    @staticmethod
    def _toggle_count(series: list[bool | str]) -> int:
        if len(series) < 2:
            return 0
        toggles = 0
        prev = series[0]
        for cur in series[1:]:
            if cur != prev:
                toggles += 1
            prev = cur
        return toggles

    def evaluate(self, obs: EpochObservation, features: FeatureVector, config: Any) -> DetectorResult:
        self.valid_history.append(bool(obs.fix_valid))
        self.fix_type_history.append(str(obs.fix_type.value))

        valid_toggles = self._toggle_count(list(self.valid_history))
        fix_type_toggles = self._toggle_count(list(self.fix_type_history))
        reacq_unstable = 1.0 if bool(features.flags.get("reacq_unstable", False)) else 0.0

        valid_norm = clamp01(valid_toggles / 6.0)
        fix_type_norm = clamp01(fix_type_toggles / 6.0)

        score = clamp01(0.45 * valid_norm + 0.35 * fix_type_norm + 0.20 * reacq_unstable)

        reason_codes: list[str] = []
        if valid_toggles >= 3:
            reason_codes.append("VALIDITY_FLAPPING")
        if fix_type_toggles >= 3:
            reason_codes.append("FIXTYPE_FLAPPING")
        if reacq_unstable > 0:
            reason_codes.append("REACQ_UNSTABLE")

        return DetectorResult(
            detector_name=self.name,
            score=score,
            hard_fail=False,
            reason_codes=reason_codes,
            metrics={
                "valid_toggle_count": float(valid_toggles),
                "fix_type_toggle_count": float(fix_type_toggles),
                "reacq_unstable": reacq_unstable,
            },
        )
