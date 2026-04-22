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
        }

        layout = QFormLayout()
        layout.addRow("Latest jump distance (m):", self._labels["jump_distance_m"])
        layout.addRow("Speed mismatch:", self._labels["speed_mismatch"])
        layout.addRow("HDOP:", self._labels["hdop"])
        layout.addRow("Stale count:", self._labels["stale_count"])
        layout.addRow("Flap count:", self._labels["flap_count"])
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
        self._labels["flap_count"].setText(str(flap_count))

    def clear(self) -> None:
        for label in self._labels.values():
            label.setText("-")
