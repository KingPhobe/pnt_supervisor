import subprocess
import sys
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "generate_meeting_figures.py"


def test_generate_meeting_figures_replay_outputs(tmp_path: Path) -> None:
    csv_path = tmp_path / "epochs.csv"
    out_dir = tmp_path / "figures"

    df = pd.DataFrame(
        {
            "t_sec": [1_747_000_000 + i for i in range(8)],
            "nav_state": ["good", "good", "recovering", "invalid", "invalid", "recovering", "good", "good"],
            "fused_score": [0.95, 0.91, 0.7, 0.4, 0.3, 0.6, 0.85, 0.9],
            "hdop": [0.8, 0.9, 1.2, 2.1, 2.4, 1.7, 1.1, 0.9],
            "num_sats": [14, 13, 12, 9, 8, 10, 12, 13],
            "fix_valid": [1, 1, 1, 0, 0, 1, 1, 1],
            "gps_speed_mps": [2.0, 2.2, 2.1, 1.6, 1.4, 1.8, 2.0, 2.1],
            "gps_accel_mps2": [0.2, 0.3, 0.1, 0.6, 0.4, 0.2, 0.1, 0.2],
            "jump_distance_m": [0.3, 0.4, 0.5, 1.2e7, 0.8, 0.7, 0.5, 0.4],
        }
    )
    df.to_csv(csv_path, index=False)

    result = subprocess.run([sys.executable, str(SCRIPT), "--csv", str(csv_path), "--out-dir", str(out_dir)], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    for name in [
        "supervisor_status_timeline.png",
        "movement_gate.png",
        "fused_score.png",
        "hdop_sats.png",
        "fix_valid_timeline.png",
    ]:
        assert (out_dir / name).exists(), f"Expected {name} to be generated"
