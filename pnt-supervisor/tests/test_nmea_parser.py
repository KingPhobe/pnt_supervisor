from __future__ import annotations

from pnt_supervisor.core.enums import FixType
from pnt_supervisor.parsers.nmea_parser import NMEAParser


def _with_checksum(body: str) -> str:
    checksum = 0
    for char in body:
        checksum ^= ord(char)
    return f"${body}*{checksum:02X}"


def test_nmea_parser_groups_epochs_and_computes_gap() -> None:
    lines = [
        _with_checksum("GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,"),
        _with_checksum("GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,,,A"),
        _with_checksum("GPGSA,A,3,04,05,09,12,24,25,29,31,,,,1.8,1.0,1.5"),
        _with_checksum("GPVTG,084.4,T,,M,005.5,N,010.2,K,A"),
        _with_checksum("GPGGA,123520,4807.040,N,01131.100,E,1,09,0.8,546.0,M,46.9,M,,"),
    ]

    parser = NMEAParser()
    observations = list(parser.parse_lines(iter(lines)))

    assert len(observations) == 2
    first, second = observations

    assert first.fix_type == FixType.FIX_3D
    assert first.fix_valid is True
    assert first.num_sats == 8
    assert first.sentence_mask > 0
    assert first.msg_gap_s == 0.0

    assert second.msg_gap_s >= first.msg_gap_s
    assert second.msg_gap_s > 0.0
    assert second.t_sec > first.t_sec
