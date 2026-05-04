"""Motion-consistency feature extraction."""

from __future__ import annotations

import math

from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.core.platform import PlatformConfig

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
    def __init__(self, platform_config: PlatformConfig | None = None) -> None:
        super().__init__(window_size=120)
        self.platform_config = platform_config or PlatformConfig()

    def extract(self, obs: EpochObservation, out: FeatureVector) -> FeatureVector:
        out = self._prepare_output(obs, out)
        prev = self.context.last_observation

        if prev is None:
            out.values.update({
                "jump_distance_m": 0.0,
                "fd_speed_mps": 0.0,
                "speed_mismatch_mps": 0.0,
                "course_track_mismatch_deg": 0.0,
                "climb_mismatch_mps": 0.0,
                "turn_rate_degps": 0.0,
            })
            out.flags.update({
                "kinematic_time_invalid": False,
                "track_geometry_ambiguous": False,
                "hover_valid": False,
                "low_motion_suspicious": False,
            })
            self.context.append(obs)
            return out

        raw_dt = obs.t_sec - prev.t_sec
        if raw_dt <= 0:
            out.values.update({
                "jump_distance_m": 0.0,
                "fd_speed_mps": 0.0,
                "speed_mismatch_mps": 0.0,
                "course_track_mismatch_deg": 0.0,
                "climb_mismatch_mps": 0.0,
                "turn_rate_degps": 0.0,
            })
            out.flags.update({
                "kinematic_time_invalid": True,
                "track_geometry_ambiguous": True,
                "hover_valid": False,
                "low_motion_suspicious": False,
            })
            self.context.append(obs)
            return out

        jump_distance_m = _haversine_m(prev.lat_deg, prev.lon_deg, obs.lat_deg, obs.lon_deg)
        fd_speed_mps = jump_distance_m / raw_dt
        speed_mismatch_mps = abs(fd_speed_mps - obs.speed_mps)
        fd_climb_mps = (obs.alt_m - prev.alt_m) / raw_dt
        climb_mismatch_mps = abs(fd_climb_mps - obs.climb_mps)
        turn_rate_degps = _angle_diff_deg(obs.course_deg, prev.course_deg) / raw_dt

        movement_too_small = (
            jump_distance_m < self.platform_config.min_track_distance_m
            and obs.speed_mps < self.platform_config.min_track_speed_mps
        )

        if movement_too_small:
            course_track_mismatch_deg = 0.0
            track_geometry_ambiguous = True
            if self.platform_config.allow_hover:
                hover_valid = True
                low_motion_suspicious = False
            else:
                hover_valid = False
                low_motion_suspicious = True
        else:
            track_deg = _bearing_deg(prev.lat_deg, prev.lon_deg, obs.lat_deg, obs.lon_deg)
            course_track_mismatch_deg = _angle_diff_deg(obs.course_deg, track_deg)
            track_geometry_ambiguous = False
            hover_valid = False
            low_motion_suspicious = False

        out.values.update({
            "jump_distance_m": jump_distance_m,
            "fd_speed_mps": fd_speed_mps,
            "speed_mismatch_mps": speed_mismatch_mps,
            "course_track_mismatch_deg": course_track_mismatch_deg,
            "climb_mismatch_mps": climb_mismatch_mps,
            "turn_rate_degps": turn_rate_degps,
        })
        out.flags.update({
            "kinematic_time_invalid": False,
            "track_geometry_ambiguous": track_geometry_ambiguous,
            "hover_valid": hover_valid,
            "low_motion_suspicious": low_motion_suspicious,
        })

        self.context.append(obs)
        return out
