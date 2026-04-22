"""XLSX replay adapter for ArduPilot-style combined logs."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from pnt_supervisor.adapters.base import ObservationAdapter
from pnt_supervisor.core.models import EpochObservation
from pnt_supervisor.parsers.xlsx_mapper import XLSXMapper


class ArduPilotLogXLSXAdapter(ObservationAdapter):
    """Replay observations from XLSX exports."""

    source_name = "xlsx_replay"

    def __init__(self, path: str | Path, sheet_name: int | str = 0) -> None:
        self.path = Path(path)
        self.sheet_name = sheet_name
        self.mapper = XLSXMapper(source_name=self.source_name)

    def reset(self) -> None:
        return None

    def iter_observations(self) -> Iterator[EpochObservation]:
        yield from self.mapper.from_file(self.path, sheet_name=self.sheet_name)
