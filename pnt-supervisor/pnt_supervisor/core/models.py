"""Core data models used by the PNT supervisor pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import FixType, NavState


@dataclass(slots=True)
class EpochObservation:
    """Normalized per-epoch observation for one navigation source."""

    t_sec: float = 0.0
    source_name: str = "unknown"
    lat_deg: float = 0.0
    lon_deg: float = 0.0
    alt_m: float = 0.0
    speed_mps: float = 0.0
    course_deg: float = 0.0
    climb_mps: float = 0.0
    fix_type: FixType = FixType.UNKNOWN
    fix_valid: bool = False
    num_sats: int = 0
    hdop: float = 99.9
    vdop: float = 99.9
    pdop: float = 99.9
    hacc_m: float = 999.0
    vacc_m: float = 999.0
    msg_gap_s: float = 0.0
    checksum_ok: bool = True
    sentence_mask: int = 0

    baro_alt_m: float | None = None
    mag_heading_deg: float | None = None
    ekf_lat_deg: float | None = None
    ekf_lon_deg: float | None = None
    ekf_alt_m: float | None = None
    ekf_speed_mps: float | None = None

    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FeatureVector:
    """Computed features consumed by detectors and fusion logic."""

    t_sec: float = 0.0
    values: dict[str, float] = field(default_factory=dict)
    flags: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DetectorResult:
    """Output from a single anomaly or integrity detector."""

    detector_name: str = "unknown"
    score: float = 0.0
    hard_fail: bool = False
    reason_codes: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class SupervisorDecision:
    """Final supervisory output for a given epoch."""

    nav_state: NavState = NavState.UNKNOWN
    nav_score: float = 1.0
    reasons: list[str] = field(default_factory=list)
    hard_fail_active: bool = False

    def __post_init__(self) -> None:
        self.nav_score = min(1.0, max(0.0, self.nav_score))
