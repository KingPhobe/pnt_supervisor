"""Shared enum definitions for the PNT supervisor core."""

from enum import Enum


class _StrEnum(str, Enum):
    """Python 3.11+ StrEnum-compatible base."""


class NavState(_StrEnum):
    """Top-level navigation quality state decided by the supervisor."""

    UNKNOWN = "unknown"
    GOOD = "good"
    DEGRADED = "degraded"
    INVALID = "invalid"
    RECOVERING = "recovering"


class SourceType(_StrEnum):
    """Supported observation source types."""

    NMEA_REPLAY = "nmea_replay"
    UBLOX_SERIAL = "ublox_serial"
    UBX_REPLAY = "ubx_replay"
    XLSX_REPLAY = "xlsx_replay"
    MAVLINK = "mavlink"


class FixType(_StrEnum):
    """Generic fix-type harmonized across source providers."""

    NONE = "none"
    NO_FIX = "no_fix"
    FIX_2D = "fix_2d"
    FIX_3D = "fix_3d"
    DGPS = "dgps"
    RTK_FLOAT = "rtk_float"
    RTK_FIXED = "rtk_fixed"
    UNKNOWN = "unknown"
