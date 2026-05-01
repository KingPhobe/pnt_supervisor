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


class SpeedAccelConsistencyConfigModel(BaseModel):
    """Configuration for GPS speed-vs-IMU acceleration consistency detector."""

    model_config = ConfigDict(extra="forbid")

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


class TimeConsistencyConfig(BaseModel):
    """Configuration for GPS time consistency checks."""

    model_config = ConfigDict(extra="forbid")

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


class AppConfig(BaseModel):
    """Top-level app configuration container."""

    model_config = ConfigDict(extra="forbid")

    vehicle: VehicleProfileConfig = Field(default_factory=VehicleProfileConfig)
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    fusion: FusionConfig = Field(default_factory=FusionConfig)
    speed_accel_consistency: SpeedAccelConsistencyConfigModel = Field(default_factory=SpeedAccelConsistencyConfigModel)
    time_consistency: TimeConsistencyConfig = Field(default_factory=TimeConsistencyConfig)
