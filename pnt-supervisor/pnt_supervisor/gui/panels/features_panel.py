"""Panel showing latest replay feature values."""

from __future__ import annotations

from PyQt6.QtWidgets import QFormLayout, QLabel, QWidget


class FeaturesPanel(QWidget):
    """Displays key feature metrics from the latest epoch."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._labels: dict[str, QLabel] = {
            "jump_distance_m": QLabel("-"),
            "speed_mismatch": QLabel("-"),
            "hdop": QLabel("-"),
            "stale_count": QLabel("-"),
            "flap_count": QLabel("-"),
            "speed_accel_residual": QLabel("-"),
            "speed_accel_ratio": QLabel("-"),
            "speed_accel_health": QLabel("-"),
            "time_dt_mismatch": QLabel("-"),
            "time_clock_drift_ppm": QLabel("-"),
            "time_clock_fit_rms": QLabel("-"),
            "time_motion_residual": QLabel("-"),
            "time_consistency_score": QLabel("-"),
        }

        layout = QFormLayout()
        layout.addRow("Latest jump distance (m):", self._labels["jump_distance_m"])
        layout.addRow("Speed mismatch:", self._labels["speed_mismatch"])
        layout.addRow("HDOP:", self._labels["hdop"])
        layout.addRow("Stale count:", self._labels["stale_count"])
        layout.addRow("Flap count:", self._labels["flap_count"])
        layout.addRow("Speed/accel residual (m/s²):", self._labels["speed_accel_residual"])
        layout.addRow("Speed/accel ratio:", self._labels["speed_accel_ratio"])
        layout.addRow("Speed/accel health:", self._labels["speed_accel_health"])
        layout.addRow("Time dt mismatch (s):", self._labels["time_dt_mismatch"])
        layout.addRow("Time clock drift (ppm):", self._labels["time_clock_drift_ppm"])
        layout.addRow("Time clock fit RMS (s):", self._labels["time_clock_fit_rms"])
        layout.addRow("Motion residual (m):", self._labels["time_motion_residual"])
        layout.addRow("Time consistency score:", self._labels["time_consistency_score"])
        self.setLayout(layout)

    def update_features(self, latest_row: dict[str, object] | None) -> None:
        if not latest_row:
            self.clear()
            return

        jump = float(latest_row.get("jump_distance_m", 0.0) or 0.0)
        speed_mismatch = float(latest_row.get("kinematic_anomaly", latest_row.get("gap_ratio", 0.0)) or 0.0)
        hdop = float(latest_row.get("hdop", 0.0) or 0.0)
        reasons = str(latest_row.get("reasons", "")).split("|")
        stale_count = sum(1 for reason in reasons if "stale" in reason.lower())
        flap_count = int(latest_row.get("state_flap_count", 0) or 0) + sum(
            1 for reason in reasons if "flap" in reason.lower()
        )

        self._labels["jump_distance_m"].setText(f"{jump:.3f}")
        self._labels["speed_mismatch"].setText(f"{speed_mismatch:.3f}")
        self._labels["hdop"].setText(f"{hdop:.3f}")
        self._labels["stale_count"].setText(str(stale_count))
        residual = float(latest_row.get("residual_mps2", 0.0) or 0.0)
        ratio = float(latest_row.get("ratio", 0.0) or 0.0)
        health = float(latest_row.get("health_score", 1.0) or 1.0)

        self._labels["flap_count"].setText(str(flap_count))
        self._labels["speed_accel_residual"].setText(f"{residual:.3f}")
        self._labels["speed_accel_ratio"].setText(f"{ratio:.3f}")
        self._labels["speed_accel_health"].setText(f"{health:.3f}")
        self._labels["time_dt_mismatch"].setText(f"{float(latest_row.get('time_dt_mismatch_s', 0.0) or 0.0):.3f}")
        self._labels["time_clock_drift_ppm"].setText(f"{float(latest_row.get('time_clock_drift_ppm', 0.0) or 0.0):.3f}")
        self._labels["time_clock_fit_rms"].setText(f"{float(latest_row.get('time_clock_fit_rms_s', 0.0) or 0.0):.3f}")
        self._labels["time_motion_residual"].setText(f"{float(latest_row.get('time_motion_residual_m', 0.0) or 0.0):.3f}")
        self._labels["time_consistency_score"].setText(f"{float(latest_row.get('detector_time_consistency_score', 0.0) or 0.0):.3f}")

    def clear(self) -> None:
        for label in self._labels.values():
            label.setText("-")
