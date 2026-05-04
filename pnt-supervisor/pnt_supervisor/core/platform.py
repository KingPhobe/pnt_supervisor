from dataclasses import dataclass
from enum import Enum


class PlatformType(str, Enum):
    UNKNOWN = "unknown"
    FIXED_WING = "fixed_wing"
    QUADCOPTER = "quadcopter"
    GROUND_VEHICLE = "ground_vehicle"


@dataclass(slots=True)
class PlatformConfig:
    platform_type: PlatformType = PlatformType.UNKNOWN
    allow_hover: bool = False
    min_track_distance_m: float = 2.0
    min_track_speed_mps: float = 0.5

    @classmethod
    def quadcopter(cls) -> "PlatformConfig":
        return cls(
            platform_type=PlatformType.QUADCOPTER,
            allow_hover=True,
        )

    @classmethod
    def fixed_wing(cls) -> "PlatformConfig":
        return cls(
            platform_type=PlatformType.FIXED_WING,
            allow_hover=False,
        )
