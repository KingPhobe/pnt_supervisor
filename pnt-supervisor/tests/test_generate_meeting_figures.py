import subprocess
import sys
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "generate_meeting_figures.py"


def test_generate_meeting_figures_replay_outputs(tmp_path: Path) -> None:
    csv_path = tmp_path / "epochs.csv"
    out_dir = tmp_path / "figures"

    base = 1_747_000_000
    df = pd.DataFrame(
        {
            "t_sec": [base, base + 1, base + 2, base + 3, base + 4, base + 30, base + 31, base + 32, base + 180, base + 181, base + 182, base + 183],
            "nav_state": ["good", "good", "recovering", "invalid", "invalid", "recovering", "good", "good", "good", "invalid", "invalid", "good"],
            "fused_score": [0.95, 0.91, 0.7, 0.4, 0.3, 0.6, 0.85, 0.9, 0.88, 0.42, 0.35, 0.82],
            "hdop": [0.8, 0.9, 1.2, 99.9, 2.4, 1.7, 1.1, 0.9, 1.0, 25.0, 3.0, 1.1],
            "num_sats": [14, 13, 12, 9, 8, 10, 12, 13, 14, 7, 8, 12],
            "fix_valid": [1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1],
            "gps_speed_mps": [2.0, 2.2, 2.1, 1.6, 1.4, 1.8, 2.0, 2.1, 2.3, 1.2, 1.3, 2.0],
            "gps_accel_mps2": [0.2, 0.3, 0.1, 0.6, 0.4, 0.2, 0.1, 0.2, 0.2, 0.7, 0.5, 0.2],
            "jump_distance_m": [0.3, 0.4, 0.5, 1.2e7, 0.8, 0.7, 0.5, 0.4, 0.3, 40.0, 35.0, 0.5],
            "reasons": [
                "",
                "None",
                "",
                "IMPOSSIBLE_JUMP|EXTREME_HDOP",
                "IMPOSSIBLE_JUMP",
                "",
                "",
                "",
                "",
                "NO_VALID_FIX_TIMEOUT",
                "EXTREME_HDOP|NO_VALID_FIX_TIMEOUT",
                "",
            ],
        }
    )
    df.to_csv(csv_path, index=False)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--csv", str(csv_path), "--out-dir", str(out_dir), "--title-prefix", "Test"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    for name in [
        "supervisor_status_timeline.png",
        "invalid_events_overview.png",
        "invalid_event_zoom_001.png",
        "fused_score.png",
        "hdop_sats.png",
        "movement_gate.png",
        "reason_codes_timeline.png",
        "fix_valid_timeline.png",
    ]:
        assert (out_dir / name).exists(), f"Expected {name} to be generated"
