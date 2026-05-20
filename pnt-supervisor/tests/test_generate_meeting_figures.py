import subprocess
import sys
from pathlib import Path

import pandas as pd


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "generate_meeting_figures.py"


def test_generate_meeting_figures_creates_expected_outputs(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    out_dir = tmp_path / "figures"

    df = pd.DataFrame(
        {
            "time_s": [0, 1, 2, 3, 4],
            "position_error_m": [0.2, 0.4, 0.8, 0.3, 0.1],
            "ground_speed_mps": [1.0, 2.0, 4.0, 2.5, 1.2],
            "accel_mps2": [0.1, 0.2, 0.3, 0.2, 0.1],
            "window_displacement_m": [0.2, 0.3, 0.6, 0.9, 0.4],
            "supervisor_status": ["OK", "OK", "WARN", "WARN", "OK"],
            "test_speed_pass": [1, 1, 0, 1, 1],
            "test_motion_ok": [True, True, True, False, True],
        }
    )
    df.to_csv(csv_path, index=False)

    cmd = [sys.executable, str(SCRIPT), "--csv", str(csv_path), "--out-dir", str(out_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    expected = [
        "position_error.png",
        "speed_accel_thresholds.png",
        "movement_gate.png",
        "test_flags_timeline.png",
        "supervisor_status_timeline.png",
    ]
    created = {p.name for p in out_dir.glob("*.png")}
    assert len(created.intersection(expected)) >= 3


def test_generate_meeting_figures_missing_optional_columns_does_not_fail(tmp_path: Path) -> None:
    csv_path = tmp_path / "minimal_results.csv"
    out_dir = tmp_path / "minimal_figures"

    df = pd.DataFrame({"time": [0, 1, 2], "position_error": [1.0, 0.8, 0.6]})
    df.to_csv(csv_path, index=False)

    cmd = [sys.executable, str(SCRIPT), "--csv", str(csv_path), "--out-dir", str(out_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert (out_dir / "position_error.png").exists()
