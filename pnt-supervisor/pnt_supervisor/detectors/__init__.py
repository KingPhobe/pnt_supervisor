"""Detectors package."""

from .base import Detector
from .hard_gates import HardGatesDetector
from .kinematic_anomaly import KinematicAnomalyDetector
from .mode_flap import ModeFlapDetector
from .stale_data import StaleDataDetector
from .speed_accel_consistency import SpeedAccelConsistencyConfig, SpeedAccelConsistencyDetector
from .statistical import StatisticalDetector
from .time_consistency import TimeConsistencyConfig, TimeConsistencyDetector

__all__ = [
    "Detector",
    "HardGatesDetector",
    "KinematicAnomalyDetector",
    "ModeFlapDetector",
    "StaleDataDetector",
    "StatisticalDetector",
    "SpeedAccelConsistencyConfig",
    "SpeedAccelConsistencyDetector",
    "TimeConsistencyConfig",
    "TimeConsistencyDetector",
]
