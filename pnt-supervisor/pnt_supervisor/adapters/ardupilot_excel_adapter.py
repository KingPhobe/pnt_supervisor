"""Excel replay adapter for ArduPilot combined logs."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from pnt_supervisor.adapters.base import ObservationAdapter
from pnt_supervisor.core.models import EpochObservation


class ArduPilotExcelObservationAdapter(ObservationAdapter):
    """Replay observations from an ArduPilot-style Excel workbook."""

    source_name = "ardupilot_excel"

    def __init__(self, path: str | Path, sheet_name: str = "in") -> None:
        self.path = Path(path)
        self.sheet_name = sheet_name

    def reset(self) -> None:
        return None

    def iter_observations(self) -> Iterator[EpochObservation]:
        df = pd.read_excel(self.path, sheet_name=self.sheet_name)

        numeric_columns = [
            "GPS_0_TimeUS",
            "timestamp",
            "GPS_0_Lat",
            "GPS_0_Lng",
            "GPS_0_Alt",
            "GPS_0_Spd",
            "GPS_0_GCrs",
            "GPS_0_VZ",
            "GPS_0_NSats",
            "GPS_0_HDop",
            "GPS_0_Status",
        ]
        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        df = df.dropna(subset=["GPS_0_Lat", "GPS_0_Lng"]).copy()

        if "GPS_0_TimeUS" in df.columns:
            df["t_sec"] = df["GPS_0_TimeUS"] / 1e6
        elif "timestamp" in df.columns:
            ts = pd.to_numeric(df["timestamp"], errors="coerce")
            start = float(ts.dropna().iloc[0]) if not ts.dropna().empty else 0.0
            df["t_sec"] = ts - start
        else:
            df["t_sec"] = pd.Series(range(len(df)), dtype="float64")

        df["t_sec"] = pd.to_numeric(df["t_sec"], errors="coerce").fillna(0.0)
        df = df.sort_values("t_sec")

        for _, row in df.iterrows():
            lat = float(row["GPS_0_Lat"])
            lon = float(row["GPS_0_Lng"])
            fix_valid = bool(row["GPS_0_Status"] >= 3) if "GPS_0_Status" in df.columns else True

            yield EpochObservation(
                t_sec=float(row["t_sec"]),
                source_name=self.source_name,
                lat_deg=lat,
                lon_deg=lon,
                alt_m=float(row.get("GPS_0_Alt", 0.0) or 0.0),
                speed_mps=float(row.get("GPS_0_Spd", 0.0) or 0.0),
                course_deg=float(row.get("GPS_0_GCrs", 0.0) or 0.0),
                climb_mps=float(row.get("GPS_0_VZ", 0.0) or 0.0),
                fix_valid=fix_valid,
                num_sats=int(row.get("GPS_0_NSats", 0) or 0),
                hdop=float(row.get("GPS_0_HDop", 99.0) or 99.0),
            )

    def __iter__(self) -> Iterator[EpochObservation]:
        return self.iter_observations()
