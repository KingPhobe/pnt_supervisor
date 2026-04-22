"""Timing and freshness related features."""

from __future__ import annotations

from pnt_supervisor.core.models import EpochObservation, FeatureVector

from .base import FeatureExtractor


class TimingFeatureExtractor(FeatureExtractor):
    def __init__(
        self,
        *,
        expected_period_s: float = 1.0,
        stale_threshold_s: float = 2.0,
        freeze_eps_deg: float = 1e-9,
    ) -> None:
        super().__init__(window_size=120)
        self.expected_period_s = expected_period_s
        self.stale_threshold_s = stale_threshold_s
        self.freeze_eps_deg = freeze_eps_deg
        self.stale_count = 0
        self.frozen_solution_count = 0

    def extract(self, obs: EpochObservation, out: FeatureVector) -> FeatureVector:
        prev = self.context.last_observation

        gap_s = max(0.0, obs.msg_gap_s)
        timestamp_backwards = False

        if prev is not None:
            dt = obs.t_sec - prev.t_sec
            if gap_s <= 0.0:
                gap_s = max(0.0, dt)
            timestamp_backwards = dt < 0.0

            frozen = (
                abs(obs.lat_deg - prev.lat_deg) <= self.freeze_eps_deg
                and abs(obs.lon_deg - prev.lon_deg) <= self.freeze_eps_deg
                and abs(obs.alt_m - prev.alt_m) <= 1e-6
            )
            if frozen:
                self.frozen_solution_count += 1
            else:
                self.frozen_solution_count = 0

        if gap_s >= self.stale_threshold_s:
            self.stale_count += 1
        else:
            self.stale_count = 0

        gap_ratio = gap_s / self.expected_period_s if self.expected_period_s > 0 else 0.0

        out.values.update(
            {
                "gap_s": gap_s,
                "gap_ratio": gap_ratio,
                "stale_count": float(self.stale_count),
                "frozen_solution_count": float(self.frozen_solution_count),
            }
        )
        out.flags["timestamp_backwards"] = timestamp_backwards

        self.context.append(obs)
        return out
