"""NMEA sentence parser that groups messages into epoch observations."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Any

import pynmea2

from pnt_supervisor.core.enums import FixType
from pnt_supervisor.core.models import EpochObservation

SENTENCE_GGA = 1 << 0
SENTENCE_RMC = 1 << 1
SENTENCE_GSA = 1 << 2
SENTENCE_VTG = 1 << 3
SENTENCE_GSV = 1 << 4
SENTENCE_ZDA = 1 << 5


@dataclass(slots=True)
class _EpochBuilder:
    timestamp: datetime
    observation: EpochObservation
    gsv_count: int = 0
    raw_sentences: list[str] = field(default_factory=list)


class NMEAParser:
    """Parse NMEA text lines and emit normalized epoch observations."""

    def __init__(self, source_name: str = "nmea_replay") -> None:
        self.source_name = source_name
        self.parse_failures = 0
        self._last_t_sec: float | None = None
        self._current_date: date | None = None

    def reset(self) -> None:
        self.parse_failures = 0
        self._last_t_sec = None
        self._current_date = None

    def parse_lines(self, lines: Iterator[str]) -> Iterator[EpochObservation]:
        current: _EpochBuilder | None = None
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            try:
                msg = pynmea2.parse(line, check=True)
            except (pynmea2.ParseError, ValueError):
                self.parse_failures += 1
                continue

            timestamp = self._extract_timestamp(msg)
            if timestamp is None:
                self.parse_failures += 1
                continue

            if current is None or current.timestamp != timestamp:
                if current is not None:
                    yield self._finalize_epoch(current.observation)
                current = _EpochBuilder(
                    timestamp=timestamp,
                    observation=EpochObservation(
                        source_name=self.source_name,
                        t_sec=timestamp.timestamp(),
                    ),
                )

            self._apply_sentence(current, msg, line)

        if current is not None:
            yield self._finalize_epoch(current.observation)

    def _extract_timestamp(self, msg: pynmea2.NMEASentence) -> datetime | None:
        had_date_before_message = self._current_date is not None
        if hasattr(msg, "datestamp") and msg.datestamp:
            self._current_date = msg.datestamp
        if hasattr(msg, "datetime") and getattr(msg, "datetime"):
            dt = getattr(msg, "datetime")
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            self._current_date = dt.date()
            if not had_date_before_message and getattr(msg, "timestamp", None) is not None:
                # Keep the first RMC epoch grouped with already-seen same-second
                # messages (e.g., GGA) when no prior date context exists.
                return datetime.combine(date(1970, 1, 1), msg.timestamp, tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        t: time | None = getattr(msg, "timestamp", None)
        if t is None:
            return None

        d = self._current_date or date(1970, 1, 1)
        return datetime.combine(d, t, tzinfo=timezone.utc)

    def _apply_sentence(self, builder: _EpochBuilder, msg: pynmea2.NMEASentence, raw: str) -> None:
        obs = builder.observation
        obs.checksum_ok = obs.checksum_ok and "*" in raw
        builder.raw_sentences.append(raw)

        sentence_type = msg.sentence_type
        if sentence_type == "GGA":
            obs.sentence_mask |= SENTENCE_GGA
            obs.lat_deg = float(msg.latitude or 0.0)
            obs.lon_deg = float(msg.longitude or 0.0)
            obs.alt_m = float(msg.altitude or 0.0)
            obs.num_sats = int(msg.num_sats or 0)
            obs.hdop = float(msg.horizontal_dil or obs.hdop)
            gga_quality = int(msg.gps_qual or 0)
            obs.fix_type = self._map_gga_quality(gga_quality)
            obs.fix_valid = gga_quality > 0
        elif sentence_type == "RMC":
            obs.sentence_mask |= SENTENCE_RMC
            obs.lat_deg = float(msg.latitude or obs.lat_deg)
            obs.lon_deg = float(msg.longitude or obs.lon_deg)
            obs.speed_mps = float(msg.spd_over_grnd or 0.0) * 0.514444
            obs.course_deg = float(msg.true_course or 0.0)
            status_valid = (msg.status or "V") == "A"
            obs.fix_valid = obs.fix_valid or status_valid
            if status_valid and obs.fix_type in {FixType.UNKNOWN, FixType.NO_FIX, FixType.NONE}:
                obs.fix_type = FixType.FIX_2D
        elif sentence_type == "GSA":
            obs.sentence_mask |= SENTENCE_GSA
            obs.pdop = float(msg.pdop or obs.pdop)
            obs.hdop = float(msg.hdop or obs.hdop)
            obs.vdop = float(msg.vdop or obs.vdop)
            mode_fix_type = int(msg.mode_fix_type or 1)
            mapped = self._map_gsa_mode(mode_fix_type)
            if mapped not in {FixType.NONE, FixType.NO_FIX}:
                obs.fix_type = mapped
                obs.fix_valid = True
            elif not obs.fix_valid:
                obs.fix_type = mapped
        elif sentence_type == "VTG":
            obs.sentence_mask |= SENTENCE_VTG
            obs.course_deg = float(msg.true_track or obs.course_deg)
            obs.speed_mps = float(msg.spd_over_grnd_kmph or 0.0) / 3.6
        elif sentence_type == "GSV":
            obs.sentence_mask |= SENTENCE_GSV
            builder.gsv_count += 1
            if getattr(msg, "num_sv_in_view", None):
                obs.num_sats = int(msg.num_sv_in_view)
        elif sentence_type == "ZDA":
            obs.sentence_mask |= SENTENCE_ZDA

    def _finalize_epoch(self, obs: EpochObservation) -> EpochObservation:
        if self._last_t_sec is None:
            obs.msg_gap_s = 0.0
        else:
            obs.msg_gap_s = max(0.0, obs.t_sec - self._last_t_sec)
        self._last_t_sec = obs.t_sec
        if obs.fix_type in {FixType.UNKNOWN, FixType.NONE} and obs.fix_valid:
            obs.fix_type = FixType.FIX_2D
        return obs

    @staticmethod
    def _map_gga_quality(quality: int) -> FixType:
        return {
            0: FixType.NO_FIX,
            1: FixType.FIX_3D,
            2: FixType.DGPS,
            4: FixType.RTK_FIXED,
            5: FixType.RTK_FLOAT,
            6: FixType.UNKNOWN,
        }.get(quality, FixType.UNKNOWN)

    @staticmethod
    def _map_gsa_mode(mode: int) -> FixType:
        return {
            1: FixType.NO_FIX,
            2: FixType.FIX_2D,
            3: FixType.FIX_3D,
        }.get(mode, FixType.UNKNOWN)
