from __future__ import annotations

from pathlib import Path

from pnt_supervisor.adapters.nmea_replay import NMEAReplayAdapter


def _with_checksum(body: str) -> str:
    checksum = 0
    for char in body:
        checksum ^= ord(char)
    return f"${body}*{checksum:02X}"


def test_nmea_adapter_skips_invalid_lines_but_counts_failures(tmp_path: Path) -> None:
    sample = "\n".join(
        [
            _with_checksum("GPGGA,010203,3723.2475,N,12158.3416,W,1,05,1.5,18.0,M,-25.7,M,,"),
            "not-a-nmea-sentence",
            _with_checksum("GPRMC,010203,A,3723.2475,N,12158.3416,W,000.5,054.7,191194,,,A"),
        ]
    )
    log_path = tmp_path / "sample.log"
    log_path.write_text(sample, encoding="utf-8")

    adapter = NMEAReplayAdapter(log_path)
    observations = list(adapter.iter_observations())

    assert len(observations) == 1
    assert adapter.parse_failures == 1
    assert observations[0].source_name == "nmea_replay"
