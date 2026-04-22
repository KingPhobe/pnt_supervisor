"""Configuration models for PNT supervisor behavior."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class VehicleProfileConfig(BaseModel):
    """Vehicle-specific constraints and expected dynamics."""

    model_config = ConfigDict(extra="forbid")

    name: str = "multirotor"
    max_speed_mps: float = 25.0
    max_climb_mps: float = 8.0
    max_turn_rate_dps: float = 120.0
    nominal_update_rate_hz: float = 10.0


class ThresholdConfig(BaseModel):
    """Thresholds used by detectors and hard-fail logic."""

    model_config = ConfigDict(extra="forbid")

    max_msg_gap_s: float = 1.5
    max_hdop: float = 2.5
    max_vdop: float = 3.5
    max_hacc_m: float = 5.0
    max_vacc_m: float = 8.0
    hard_fail_score: float = 0.95


class FusionConfig(BaseModel):
    """Fusion and decision policy tuning values."""

    model_config = ConfigDict(extra="forbid")

    score_decay_per_s: float = 0.2
    hard_fail_hold_s: float = 3.0
    recovering_threshold: float = 0.6
    good_threshold: float = 0.85
    detector_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "kinematics": 0.35,
            "consistency": 0.35,
            "signal_quality": 0.30,
        }
    )


class AppConfig(BaseModel):
    """Top-level app configuration container."""

    model_config = ConfigDict(extra="forbid")

    vehicle: VehicleProfileConfig = Field(default_factory=VehicleProfileConfig)
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    fusion: FusionConfig = Field(default_factory=FusionConfig)
