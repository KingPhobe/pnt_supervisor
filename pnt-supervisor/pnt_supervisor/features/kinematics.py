"""Motion-consistency feature extraction."""

from __future__ import annotations

import math

from pnt_supervisor.core.models import EpochObservation, FeatureVector

from .base import FeatureExtractor

EARTH_RADIUS_M = 6371000.0


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def _bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def _angle_diff_deg(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


class KinematicFeatureExtractor(FeatureExtractor):
    def __init__(self) -> None:
        super().__init__(window_size=120)

    def extract(self, obs: EpochObservation, out: FeatureVector) -> FeatureVector:
        prev = self.context.last_observation

        jump_distance_m = 0.0
        fd_speed_mps = 0.0
        speed_mismatch_mps = 0.0
        course_track_mismatch_deg = 0.0
        climb_mismatch_mps = 0.0
        turn_rate_degps = 0.0

        if prev is not None:
            dt = max(1e-6, obs.t_sec - prev.t_sec)
            jump_distance_m = _haversine_m(prev.lat_deg, prev.lon_deg, obs.lat_deg, obs.lon_deg)
            fd_speed_mps = jump_distance_m / dt
            speed_mismatch_mps = abs(fd_speed_mps - obs.speed_mps)

            track_deg = _bearing_deg(prev.lat_deg, prev.lon_deg, obs.lat_deg, obs.lon_deg)
            course_track_mismatch_deg = _angle_diff_deg(obs.course_deg, track_deg)

            fd_climb_mps = (obs.alt_m - prev.alt_m) / dt
            climb_mismatch_mps = abs(fd_climb_mps - obs.climb_mps)

            turn_rate_degps = _angle_diff_deg(obs.course_deg, prev.course_deg) / dt

        out.values.update(
            {
                "jump_distance_m": jump_distance_m,
                "fd_speed_mps": fd_speed_mps,
                "speed_mismatch_mps": speed_mismatch_mps,
                "course_track_mismatch_deg": course_track_mismatch_deg,
                "climb_mismatch_mps": climb_mismatch_mps,
                "turn_rate_degps": turn_rate_degps,
            }
        )

        self.context.append(obs)
        return out
