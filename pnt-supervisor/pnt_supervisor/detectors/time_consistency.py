"""Detector for GPS time consistency anomalies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector

from .base import Detector, clamp01


@dataclass(slots=True)
class TimeConsistencyConfig:
    enabled: bool = True
    window_s: float = 10.0
    min_samples: int = 5
    max_gps_time_gap_s: float = 2.0
    max_gps_time_jump_s: float = 1.5
    max_time_backwards_s: float = 0.05
    max_time_freeze_s: float = 2.0
    max_dt_mismatch_s: float = 0.25
    max_clock_drift_ppm: float = 50.0
    max_clock_residual_rms_s: float = 0.20
    min_speed_for_motion_check_mps: float = 3.0
    max_motion_time_residual_m: float = 10.0
    max_implied_time_residual_s: float = 1.0
    fault_score_threshold: float = 0.8
    consecutive_windows_to_fault: int = 3


class TimeConsistencyDetector(Detector):
    name = "time_consistency"

    def __init__(self, cfg: TimeConsistencyConfig | None = None) -> None:
        self.cfg = cfg or TimeConsistencyConfig()
        self._consecutive_fault = 0

    def evaluate(self, obs: EpochObservation, features: FeatureVector, config: Any) -> DetectorResult:
        _ = config
        dt_mismatch_s = float(features.values.get("time_dt_mismatch_s", 0.0) or 0.0)
        dt_gps_s = float(features.values.get("time_dt_gps_s", 0.0) or 0.0)
        jump_s = float(features.values.get("time_gps_time_jump_s", 0.0) or 0.0)
        drift_ppm = abs(float(features.values.get("time_clock_drift_ppm", 0.0) or 0.0))
        fit_rms_s = float(features.values.get("time_clock_fit_rms_s", 0.0) or 0.0)
        motion_residual_m = float(features.values.get("time_motion_residual_m", 0.0) or 0.0)
        implied_residual_s = float(features.values.get("time_implied_residual_s", 0.0) or 0.0)
        backwards = bool(features.flags.get("time_gps_time_backwards", False))
        frozen = bool(features.flags.get("time_gps_time_frozen", False))
        fit_available = bool(features.flags.get("time_fit_available", False))

        dt_score = clamp01(dt_mismatch_s / self.cfg.max_dt_mismatch_s)
        drift_score = clamp01(drift_ppm / self.cfg.max_clock_drift_ppm) if fit_available else 0.0
        rms_score = clamp01(fit_rms_s / self.cfg.max_clock_residual_rms_s) if fit_available else 0.0

        motion_enabled = obs.speed_mps >= self.cfg.min_speed_for_motion_check_mps
        motion_score = clamp01(motion_residual_m / self.cfg.max_motion_time_residual_m) if motion_enabled else 0.0
        implied_score = clamp01(implied_residual_s / self.cfg.max_implied_time_residual_s) if motion_enabled else 0.0

        freeze_score = 1.0 if frozen and dt_gps_s <= self.cfg.max_time_freeze_s else 0.0
        backwards_score = 1.0 if backwards else 0.0
        jump_score = clamp01(jump_s / self.cfg.max_gps_time_jump_s)

        score = clamp01(
            0.20 * dt_score
            + 0.15 * drift_score
            + 0.10 * rms_score
            + 0.20 * motion_score
            + 0.15 * implied_score
            + 0.10 * freeze_score
            + 0.10 * max(backwards_score, jump_score)
        )

        severe_backwards = backwards and abs(dt_gps_s) > self.cfg.max_time_backwards_s
        if severe_backwards:
            self._consecutive_fault = self.cfg.consecutive_windows_to_fault
        elif score >= self.cfg.fault_score_threshold:
            self._consecutive_fault += 1
        else:
            self._consecutive_fault = 0

        hard_fail = severe_backwards or self._consecutive_fault >= self.cfg.consecutive_windows_to_fault

        reasons: list[str] = []
        if severe_backwards:
            reasons.append("GPS_TIME_BACKWARDS_SEVERE")
        elif backwards:
            reasons.append("GPS_TIME_BACKWARDS")
        if frozen:
            reasons.append("GPS_TIME_FROZEN")
        if dt_mismatch_s > self.cfg.max_dt_mismatch_s:
            reasons.append("GPS_LOG_DT_MISMATCH")
        if fit_available and drift_ppm > self.cfg.max_clock_drift_ppm:
            reasons.append("CLOCK_DRIFT_HIGH")
        if fit_available and fit_rms_s > self.cfg.max_clock_residual_rms_s:
            reasons.append("CLOCK_FIT_RMS_HIGH")
        if motion_enabled and motion_residual_m > self.cfg.max_motion_time_residual_m:
            reasons.append("MOTION_TIME_RESIDUAL_HIGH")

        return DetectorResult(
            detector_name=self.name,
            score=score,
            hard_fail=hard_fail,
            reason_codes=reasons,
            metrics={
                "time_dt_mismatch_s": dt_mismatch_s,
                "time_clock_drift_ppm": drift_ppm,
                "time_clock_fit_rms_s": fit_rms_s,
                "time_motion_residual_m": motion_residual_m,
                "time_implied_residual_s": implied_residual_s,
                "consecutive_fault_windows": float(self._consecutive_fault),
            },
        )
