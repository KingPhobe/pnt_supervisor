from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _write_tiny_xlsx(path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "timestamp": 1000.0,
                "GPS_0_Lat": 37.77490,
                "GPS_0_Lng": -122.41940,
                "GPS_0_Alt": 10.0,
                "GPS_0_Spd": 8.0,
                "GPS_0_GCrs": 90.0,
                "GPS_0_VZ": 0.0,
                "GPS_0_Status": 3,
                "GPS_0_NSats": 12,
                "GPS_0_HDop": 0.8,
                "GPA_0_HAcc": 0.6,
                "GPA_0_VAcc": 0.9,
            },
            {
                "timestamp": 1001.0,
                "GPS_0_Lat": 37.77495,
                "GPS_0_Lng": -122.41945,
                "GPS_0_Alt": 10.2,
                "GPS_0_Spd": 8.1,
                "GPS_0_GCrs": 91.0,
                "GPS_0_VZ": 0.1,
                "GPS_0_Status": 3,
                "GPS_0_NSats": 12,
                "GPS_0_HDop": 0.8,
                "GPA_0_HAcc": 0.6,
                "GPA_0_VAcc": 0.9,
            },
        ]
    )
    df.to_excel(path, index=False)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_end_to_end_demo_runner_generates_outputs(tmp_path: Path) -> None:
    input_xlsx = tmp_path / "tiny_input.xlsx"
    output_dir = tmp_path / "demo_out"
    _write_tiny_xlsx(input_xlsx)

    cmd = [
        sys.executable,
        "scripts/run_replay_demo.py",
        "--input",
        str(input_xlsx),
        "--source-type",
        "xlsx",
        "--out-dir",
        str(output_dir),
    ]

    completed = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], check=True, capture_output=True, text=True)
    assert "Replay completed." in completed.stdout

    epochs_path = output_dir / "epochs.csv"
    events_path = output_dir / "events.csv"
    summary_path = output_dir / "summary.json"

    assert epochs_path.exists()
    assert events_path.exists()
    assert summary_path.exists()

    epoch_rows = _read_rows(epochs_path)
    assert epoch_rows
    assert any(row["nav_state"] in {"good", "recovering", "degraded", "invalid", "unknown"} for row in epoch_rows)
