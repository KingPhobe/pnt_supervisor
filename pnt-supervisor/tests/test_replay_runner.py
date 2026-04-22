import csv
import json
from pathlib import Path

from pnt_supervisor.adapters.base import ObservationAdapter
from pnt_supervisor.core.enums import FixType
from pnt_supervisor.core.models import EpochObservation
from pnt_supervisor.evaluation import ReplayRunner


class SyntheticAdapter(ObservationAdapter):
    def __init__(self, observations: list[EpochObservation]) -> None:
        self._observations = observations

    def reset(self) -> None:
        return None

    def iter_observations(self):
        yield from self._observations


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_replay_runner_creates_exports_and_summary(tmp_path: Path) -> None:
    obs = [
        EpochObservation(
            t_sec=0.0,
            source_name="synthetic",
            fix_valid=True,
            fix_type=FixType.FIX_3D,
            lat_deg=37.0,
            lon_deg=-122.0,
            alt_m=10.0,
            speed_mps=1.0,
            msg_gap_s=1.0,
            hdop=0.9,
            num_sats=10,
        ),
        EpochObservation(
            t_sec=1.0,
            source_name="synthetic",
            fix_valid=True,
            fix_type=FixType.FIX_3D,
            lat_deg=37.000009,
            lon_deg=-122.0,
            alt_m=10.1,
            speed_mps=1.0,
            msg_gap_s=1.0,
            hdop=0.9,
            num_sats=10,
        ),
        EpochObservation(
            t_sec=2.0,
            source_name="synthetic",
            fix_valid=False,
            fix_type=FixType.NO_FIX,
            lat_deg=37.8,
            lon_deg=-122.0,
            alt_m=10.1,
            speed_mps=1.0,
            msg_gap_s=4.0,
            hdop=15.0,
            num_sats=2,
        ),
        EpochObservation(
            t_sec=3.0,
            source_name="synthetic",
            fix_valid=True,
            fix_type=FixType.FIX_3D,
            lat_deg=37.000027,
            lon_deg=-122.0,
            alt_m=10.2,
            speed_mps=1.0,
            msg_gap_s=1.0,
            hdop=0.8,
            num_sats=11,
        ),
    ]

    runner = ReplayRunner(SyntheticAdapter(obs))
    result = runner.run(tmp_path)

    epochs_path = tmp_path / "epochs.csv"
    events_path = tmp_path / "events.csv"
    summary_path = tmp_path / "summary.json"

    assert result.output_paths["epochs_csv"] == epochs_path
    assert result.output_paths["events_csv"] == events_path
    assert result.output_paths["summary_json"] == summary_path

    assert epochs_path.exists()
    assert events_path.exists()
    assert summary_path.exists()

    epoch_rows = _load_csv(epochs_path)
    assert epoch_rows
    assert "nav_state" in epoch_rows[0]
    assert "fused_score" in epoch_rows[0]

    event_rows = _load_csv(events_path)
    assert event_rows
    assert any(row["from_state"] != row["to_state"] for row in event_rows)

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["total_epochs"] == len(obs)
    assert "state_dwell_times_s" in summary
    assert "invalid_events" in summary
    assert "degraded_events" in summary
    assert "reason_histogram" in summary
