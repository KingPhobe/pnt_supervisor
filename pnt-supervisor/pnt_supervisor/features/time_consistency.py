"""GPS time consistency feature extraction."""

from __future__ import annotations

from collections import deque
import math

from pnt_supervisor.core.models import EpochObservation, FeatureVector

from .base import FeatureExtractor

EARTH_RADIUS_M = 6371000.0


class TimeConsistencyFeatureExtractor(FeatureExtractor):
    def __init__(self, *, window_s: float = 10.0, min_samples: int = 5) -> None:
        super().__init__(window_size=max(120, min_samples * 4))
        self.window_s = window_s
        self.min_samples = min_samples
        self._samples: deque[tuple[float, float]] = deque()

    def extract(self, obs: EpochObservation, out: FeatureVector) -> FeatureVector:
        prev = self.context.last_observation
        gps_time_s = self._gps_time(obs)

        dt_log_s = 0.0
        dt_gps_s = 0.0
        dt_mismatch_s = 0.0
        backwards = False
        frozen = False
        jump_s = 0.0
        pos_delta_m = 0.0
        expected_distance_m = 0.0
        motion_residual_m = 0.0
        implied_dt_s = 0.0
        implied_time_residual_s = 0.0

        if prev is not None:
            prev_gps_time_s = self._gps_time(prev)
            dt_log_s = obs.t_sec - prev.t_sec
            dt_gps_s = gps_time_s - prev_gps_time_s
            dt_mismatch_s = abs(dt_gps_s - dt_log_s)
            backwards = dt_gps_s < 0.0
            frozen = abs(dt_gps_s) <= 1e-9
            jump_s = abs(dt_gps_s)

            pos_delta_m = self._distance_3d_m(obs, prev)
            expected_distance_m = max(0.0, obs.speed_mps) * max(0.0, dt_gps_s)

            if obs.speed_mps > 1e-6:
                implied_dt_s = pos_delta_m / obs.speed_mps
                implied_time_residual_s = abs(implied_dt_s - max(0.0, dt_gps_s))
            motion_residual_m = abs(pos_delta_m - expected_distance_m)

        self.context.append(obs)
        self._samples.append((obs.t_sec, gps_time_s))
        self._evict_window(obs.t_sec)

        time_fit_available = len(self._samples) >= self.min_samples
        drift_ppm = 0.0
        fit_rms_s = 0.0
        if time_fit_available:
            slope, intercept = self._fit_line(self._samples)
            drift_ppm = (slope - 1.0) * 1e6
            fit_rms_s = self._fit_rms(self._samples, slope, intercept)

        out.values.update(
            {
                "time_dt_gps_s": dt_gps_s,
                "time_dt_log_s": dt_log_s,
                "time_dt_mismatch_s": dt_mismatch_s,
                "time_gps_time_jump_s": jump_s,
                "time_position_delta_3d_m": pos_delta_m,
                "time_expected_distance_from_speed_m": expected_distance_m,
                "time_motion_residual_m": motion_residual_m,
                "time_implied_dt_from_motion_s": implied_dt_s,
                "time_implied_residual_s": implied_time_residual_s,
                "time_clock_drift_ppm": drift_ppm,
                "time_clock_fit_rms_s": fit_rms_s,
            }
        )
        out.flags["time_gps_time_backwards"] = backwards
        out.flags["time_gps_time_frozen"] = frozen
        out.flags["time_fit_available"] = time_fit_available
        return out

    def _evict_window(self, t_sec: float) -> None:
        while self._samples and (t_sec - self._samples[0][0]) > self.window_s:
            self._samples.popleft()

    def _gps_time(self, obs: EpochObservation) -> float:
        if "gps_time_s" in obs.extras:
            try:
                return float(obs.extras["gps_time_s"])
            except (TypeError, ValueError):
                pass
        return float(obs.t_sec)

    def _fit_line(self, samples: deque[tuple[float, float]]) -> tuple[float, float]:
        xs = [x for x, _ in samples]
        ys = [y for _, y in samples]
        n = len(xs)
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=False))
        den = sum((x - x_mean) ** 2 for x in xs)
        if den <= 1e-9:
            return 1.0, 0.0
        slope = num / den
        intercept = y_mean - slope * x_mean
        return slope, intercept

    def _fit_rms(self, samples: deque[tuple[float, float]], slope: float, intercept: float) -> float:
        if not samples:
            return 0.0
        err2 = [(y - (slope * x + intercept)) ** 2 for x, y in samples]
        return math.sqrt(sum(err2) / len(err2))

    def _distance_3d_m(self, a: EpochObservation, b: EpochObservation) -> float:
        lat1 = math.radians(a.lat_deg)
        lon1 = math.radians(a.lon_deg)
        lat2 = math.radians(b.lat_deg)
        lon2 = math.radians(b.lon_deg)
        dlat = lat1 - lat2
        dlon = lon1 - lon2
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        horizontal = 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(max(0.0, h))))
        dz = a.alt_m - b.alt_m
        return math.sqrt(horizontal * horizontal + dz * dz)
