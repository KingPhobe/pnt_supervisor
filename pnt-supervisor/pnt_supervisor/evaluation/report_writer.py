"""Writers for replay runner outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pnt_supervisor.exports import CsvWriter, JsonWriter


class ReplayReportWriter:
    """Persist replay outputs as CSV/JSON artifacts."""

    def __init__(self, csv_writer: CsvWriter | None = None, json_writer: JsonWriter | None = None) -> None:
        self.csv_writer = csv_writer or CsvWriter()
        self.json_writer = json_writer or JsonWriter()

    def write(
        self,
        output_dir: Path,
        *,
        epoch_rows: list[dict[str, Any]],
        event_rows: list[dict[str, Any]],
        summary: dict[str, Any],
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)

        epoch_fields = list(epoch_rows[0].keys()) if epoch_rows else [
            "t_sec",
            "source_name",
            "fix_valid",
            "num_sats",
            "hdop",
            "msg_gap_s",
            "jump_distance_m",
            "gap_ratio",
            "state_flap_count",
            "hard_gates",
            "kinematic_anomaly",
            "stale_data",
            "mode_flap",
            "statistical",
            "fused_score",
            "nav_state",
            "reasons",
        ]
        event_fields = list(event_rows[0].keys()) if event_rows else ["t_sec", "from_state", "to_state", "reason"]

        epochs_path = self.csv_writer.write_rows(output_dir / "epochs.csv", epoch_rows, epoch_fields)
        events_path = self.csv_writer.write_rows(output_dir / "events.csv", event_rows, event_fields)
        summary_path = self.json_writer.write(output_dir / "summary.json", summary)

        return {
            "epochs_csv": epochs_path,
            "events_csv": events_path,
            "summary_json": summary_path,
        }
