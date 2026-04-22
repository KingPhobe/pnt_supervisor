"""NMEA replay adapter from plain text/log files."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from pnt_supervisor.adapters.base import ObservationAdapter
from pnt_supervisor.core.models import EpochObservation
from pnt_supervisor.parsers.nmea_parser import NMEAParser

_ALLOWED_SUFFIXES = {".txt", ".log", ".nmea"}


class NMEAReplayAdapter(ObservationAdapter):
    """Replay NMEA logs from text-like files."""

    source_name = "nmea_replay"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if self.path.suffix.lower() not in _ALLOWED_SUFFIXES:
            raise ValueError(f"Unsupported NMEA replay extension: {self.path.suffix}")
        self.parser = NMEAParser(source_name=self.source_name)
        self.parse_failures = 0

    def reset(self) -> None:
        self.parser.reset()
        self.parse_failures = 0

    def iter_observations(self) -> Iterator[EpochObservation]:
        with self.path.open("r", encoding="utf-8", errors="replace") as handle:
            for obs in self.parser.parse_lines(handle):
                yield obs
        self.parse_failures = self.parser.parse_failures
