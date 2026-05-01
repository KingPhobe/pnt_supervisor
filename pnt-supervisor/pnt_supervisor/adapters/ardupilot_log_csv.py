"""CSV replay adapter for ArduPilot-style combined logs."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from pnt_supervisor.adapters.base import ObservationAdapter
from pnt_supervisor.core.models import EpochObservation
from pnt_supervisor.parsers.xlsx_mapper import XLSXMapper


class ArduPilotLogCSVAdapter(ObservationAdapter):
    """Replay observations from CSV exports."""

    source_name = "csv_replay"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.mapper = XLSXMapper(source_name=self.source_name)

    def reset(self) -> None:
        return None

    def iter_observations(self) -> Iterator[EpochObservation]:
        df = pd.read_csv(self.path)
        yield from self.mapper.from_dataframe(df)
