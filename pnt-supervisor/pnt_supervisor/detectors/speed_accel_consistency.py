"""Scalar GPS speed-vs-IMU acceleration consistency detector."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import median
from typing import Any

import math

from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector

from .base import Detector, clamp01


@dataclass(slots=True)
class SpeedAccelConsistencyConfig:
    """Configuration for speed-vs-accel consistency checks."""

    enabled: bool = False
    window_s: float = 5.0
    min_samples: int = 5
    gravity_mps2: float = 9.80665
    imu_noise_floor_mps2: float = 0.25
    warning_residual_mps2: float = 1.5
    fault_residual_mps2: float = 3.0
    warning_ratio: float = 2.0
    fault_ratio: float = 3.5
    consecutive_windows_to_flag: int = 3
    eps: float = 1e-6
    imu_window_stat: str = "median"
    time_column: str = "timestamp"
    gps_speed_column: str = "GPS_0_Spd"
    accel_x_column: str = "IMU_AccX"
    accel_y_column: str = "IMU_AccY"
    accel_z_column: str = "IMU_AccZ"


@dataclass(slots=True)
class SpeedAccelConsistencyResult:
    """Per-epoch detector output."""

    t_s: float
    gps_speed_mps: float
    gps_accel_mps2: float
    imu_dynamic_accel_mps2: float
    residual_mps2: float
    ratio: float
    warning_flag: bool
    fault_flag: bool
    health_score: float
    reason: str
    decision_available: bool


class SpeedAccelConsistencyDetector(Detector):
    """Compare GPS-derived scalar acceleration against IMU-derived dynamic acceleration."""

    name = "speed_accel_consistency"

    def __init__(self, config: SpeedAccelConsistencyConfig | None = None) -> None:
        self.cfg = config or SpeedAccelConsistencyConfig()
        self._window: deque[tuple[float, float, float, bool]] = deque()
        self._consecutive_warning = 0
        self._consecutive_fault = 0

    def evaluate(self, obs: EpochObservation, features: FeatureVector, config: Any) -> DetectorResult:
        _ = features

        t_s = self._read_value(obs, self.cfg.time_column, fallback=obs.t_sec)
        gps_speed_mps = self._read_value(obs, self.cfg.gps_speed_column, fallback=obs.speed_mps)

        ax = self._read_optional(obs, self.cfg.accel_x_column)
        ay = self._read_optional(obs, self.cfg.accel_y_column)
        az = self._read_optional(obs, self.cfg.accel_z_column)

        imu_dynamic = self._calc_imu_dynamic(ax, ay, az)
        sample_valid = imu_dynamic is not None and math.isfinite(gps_speed_mps)
        self._window.append((t_s, gps_speed_mps, float(imu_dynamic or 0.0), sample_valid))
        self._evict_old(t_s)

        result = self._compute_result(t_s=t_s, gps_speed_mps=gps_speed_mps)

        return DetectorResult(
            detector_name=self.name,
            score=clamp01(1.0 - result.health_score),
            hard_fail=result.fault_flag,
            reason_codes=[result.reason] if result.reason else [],
            metrics={
                "t_s": result.t_s,
                "gps_speed_mps": result.gps_speed_mps,
                "gps_accel_mps2": result.gps_accel_mps2,
                "imu_dynamic_accel_mps2": result.imu_dynamic_accel_mps2,
                "residual_mps2": result.residual_mps2,
                "ratio": result.ratio,
                "warning_flag": float(result.warning_flag),
                "fault_flag": float(result.fault_flag),
                "health_score": result.health_score,
                "decision_available": float(result.decision_available),
            },
        )

    def _compute_result(self, *, t_s: float, gps_speed_mps: float) -> SpeedAccelConsistencyResult:
        valid_samples = [sample for sample in self._window if sample[3]]
        if len(valid_samples) < self.cfg.min_samples:
            self._consecutive_warning = 0
            self._consecutive_fault = 0
            return SpeedAccelConsistencyResult(
                t_s=t_s,
                gps_speed_mps=gps_speed_mps,
                gps_accel_mps2=0.0,
                imu_dynamic_accel_mps2=0.0,
                residual_mps2=0.0,
                ratio=0.0,
                warning_flag=False,
                fault_flag=False,
                health_score=0.5,
                reason="NO_DECISION_INSUFFICIENT_VALID_SAMPLES",
                decision_available=False,
            )

        times = [sample[0] for sample in valid_samples]
        speeds = [sample[1] for sample in valid_samples]
        imu_dyn_values = [sample[2] for sample in valid_samples]

        gps_accel = self._slope(times, speeds)
        imu_dynamic = self._window_stat(imu_dyn_values)

        abs_gps_accel = abs(gps_accel)
        residual = abs(abs_gps_accel - imu_dynamic)
        ratio = abs_gps_accel / max(imu_dynamic + self.cfg.imu_noise_floor_mps2, self.cfg.eps)

        warn_now = residual >= self.cfg.warning_residual_mps2 or ratio >= self.cfg.warning_ratio
        fault_now = residual >= self.cfg.fault_residual_mps2 or ratio >= self.cfg.fault_ratio

        self._consecutive_warning = self._consecutive_warning + 1 if warn_now else 0
        self._consecutive_fault = self._consecutive_fault + 1 if fault_now else 0

        warning_flag = self._consecutive_warning >= self.cfg.consecutive_windows_to_flag
        fault_flag = self._consecutive_fault >= self.cfg.consecutive_windows_to_flag

        if fault_flag:
            reason = "GPS_IMU_ACCEL_MISMATCH_FAULT"
        elif warning_flag:
            reason = "GPS_IMU_ACCEL_MISMATCH_WARNING"
        else:
            reason = "GPS_IMU_ACCEL_CONSISTENT"

        residual_health = clamp01(1.0 - residual / max(self.cfg.fault_residual_mps2, self.cfg.eps))
        ratio_health = clamp01(1.0 - max(0.0, ratio - 1.0) / max(self.cfg.fault_ratio - 1.0, self.cfg.eps))
        health_score = clamp01(0.5 * residual_health + 0.5 * ratio_health)

        return SpeedAccelConsistencyResult(
            t_s=t_s,
            gps_speed_mps=gps_speed_mps,
            gps_accel_mps2=gps_accel,
            imu_dynamic_accel_mps2=imu_dynamic,
            residual_mps2=residual,
            ratio=ratio,
            warning_flag=warning_flag,
            fault_flag=fault_flag,
            health_score=health_score,
            reason=reason,
            decision_available=True,
        )

    def _window_stat(self, values: list[float]) -> float:
        if not values:
            return 0.0
        if self.cfg.imu_window_stat.lower() == "rms":
            return math.sqrt(sum(v * v for v in values) / len(values))
        return float(median(values))

    def _slope(self, times: list[float], values: list[float]) -> float:
        n = len(times)
        if n < 2:
            return 0.0
        mean_t = sum(times) / n
        mean_v = sum(values) / n
        num = sum((t - mean_t) * (v - mean_v) for t, v in zip(times, values, strict=False))
        den = sum((t - mean_t) ** 2 for t in times)
        if den <= self.cfg.eps:
            return 0.0
        return num / den

    def _calc_imu_dynamic(self, ax: float | None, ay: float | None, az: float | None) -> float | None:
        if ax is None or ay is None or az is None:
            return None
        acc_norm = math.sqrt(ax * ax + ay * ay + az * az)
        return abs(acc_norm - self.cfg.gravity_mps2)

    def _evict_old(self, t_s: float) -> None:
        while self._window and (t_s - self._window[0][0]) > self.cfg.window_s:
            self._window.popleft()

    def _read_optional(self, obs: EpochObservation, column: str) -> float | None:
        if hasattr(obs, column):
            value = getattr(obs, column)
            return float(value) if value is not None else None

        value = obs.extras.get(column)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _read_value(self, obs: EpochObservation, column: str, fallback: float) -> float:
        value = self._read_optional(obs, column)
        return float(value) if value is not None else float(fallback)
