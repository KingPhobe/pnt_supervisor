from __future__ import annotations

import subprocess
import sys

import pandas as pd


def test_run_replay_cli_writes_outputs(tmp_path) -> None:
    input_path = tmp_path / "input.xlsx"
    out_dir = tmp_path / "meeting_output"

    pd.DataFrame(
        [
            {
                "GPS_0_TimeUS": 1_000_000,
                "GPS_0_Lat": 37.4,
                "GPS_0_Lng": -122.2,
                "GPS_0_Alt": 10.0,
                "GPS_0_Status": 3,
            },
            {
                "GPS_0_TimeUS": 2_000_000,
                "GPS_0_Lat": 37.4001,
                "GPS_0_Lng": -122.2001,
                "GPS_0_Alt": 10.1,
                "GPS_0_Status": 4,
            },
        ]
    ).to_excel(input_path, sheet_name="in", index=False)

    cmd = [
        sys.executable,
        "-m",
        "pnt_supervisor.evaluation.run_replay",
        "--input",
        str(input_path),
        "--input-format",
        "ardupilot_excel",
        "--sheet",
        "in",
        "--out-dir",
        str(out_dir),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "Output directory:" in completed.stdout
    assert out_dir.exists()
    assert any(path.is_file() for path in out_dir.iterdir())
    assert (out_dir / "epochs.csv").exists()
