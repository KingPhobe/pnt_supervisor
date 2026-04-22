"""Helpers for mapping ArduPilot-style XLSX logs into normalized observations."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pandas as pd

from pnt_supervisor.core.enums import FixType
from pnt_supervisor.core.models import EpochObservation

_REQUIRED_COLUMN_MAP = {
    "GPS_0_Lat": "lat_deg",
    "GPS_0_Lng": "lon_deg",
    "GPS_0_Alt": "alt_m",
    "GPS_0_Spd": "speed_mps",
    "GPS_0_GCrs": "course_deg",
    "GPS_0_VZ": "climb_mps",
    "GPS_0_NSats": "num_sats",
    "GPS_0_HDop": "hdop",
    "GPA_0_HAcc": "hacc_m",
    "GPA_0_VAcc": "vacc_m",
}

_OPTIONAL_COLUMN_MAP = {
    "BARO_Alt": "baro_alt_m",
    "MAG_Heading": "mag_heading_deg",
    "XKF1_Lat": "ekf_lat_deg",
    "XKF1_Lon": "ekf_lon_deg",
    "XKF1_Alt": "ekf_alt_m",
    "XKF1_Spd": "ekf_speed_mps",
}


class XLSXMapper:
    """Map XLSX rows into :class:`EpochObservation` records."""

    def __init__(self, source_name: str = "xlsx_replay") -> None:
        self.source_name = source_name

    def from_file(self, path: str | Path, sheet_name: int | str = 0) -> Iterator[EpochObservation]:
        df = pd.read_excel(path, sheet_name=sheet_name)
        yield from self.from_dataframe(df)

    def from_dataframe(self, dataframe: pd.DataFrame) -> Iterator[EpochObservation]:
        known_columns = {"timestamp", "GPS_0_Status", *_REQUIRED_COLUMN_MAP.keys(), *_OPTIONAL_COLUMN_MAP.keys()}

        for idx, row in dataframe.iterrows():
            obs = EpochObservation(source_name=self.source_name)
            obs.t_sec = _coerce_timestamp(row.get("timestamp"), fallback=float(idx))

            for column, attr in _REQUIRED_COLUMN_MAP.items():
                value = row.get(column)
                if pd.notna(value):
                    setattr(obs, attr, _cast_value(attr, value))

            status = row.get("GPS_0_Status")
            if pd.notna(status):
                obs.fix_type = _map_status_to_fix_type(int(status))
                obs.fix_valid = obs.fix_type not in {FixType.NO_FIX, FixType.NONE, FixType.UNKNOWN}

            for column, attr in _OPTIONAL_COLUMN_MAP.items():
                value = row.get(column)
                if pd.notna(value):
                    setattr(obs, attr, float(value))

            obs.extras = {
                str(column): _to_builtin(value)
                for column, value in row.items()
                if column not in known_columns and pd.notna(value)
            }
            yield obs


def _coerce_timestamp(value: object, fallback: float) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.timestamp()
    if isinstance(value, datetime):
        return value.timestamp()
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.notna(parsed):
        return parsed.timestamp()
    return fallback


def _map_status_to_fix_type(status: int) -> FixType:
    return {
        0: FixType.NO_FIX,
        1: FixType.NO_FIX,
        2: FixType.FIX_2D,
        3: FixType.FIX_3D,
        4: FixType.DGPS,
        5: FixType.RTK_FLOAT,
        6: FixType.RTK_FIXED,
    }.get(status, FixType.UNKNOWN)


def _cast_value(attr: str, value: object) -> object:
    if attr == "num_sats":
        return int(value)
    return float(value)


def _to_builtin(value: object) -> object:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value.item() if hasattr(value, "item") else value
