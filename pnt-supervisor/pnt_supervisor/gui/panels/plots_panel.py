"""Panel with one-at-a-time matplotlib metric plots."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QComboBox, QVBoxLayout, QWidget


class PlotsPanel(QWidget):
    """Renders selectable replay metrics on a single matplotlib axes."""

    METRICS: dict[str, str] = {
        "fused score": "fused_score",
        "jump distance": "jump_distance_m",
        "HDOP": "hdop",
        "num_sats": "num_sats",
        "GPS accel": "gps_accel_mps2",
        "IMU dynamic accel": "imu_dynamic_accel_mps2",
        "speed/accel residual": "residual_mps2",
        "speed/accel ratio": "ratio",
        "time consistency score": "detector_time_consistency_score",
        "clock drift ppm": "time_clock_drift_ppm",
        "motion-time residual": "time_motion_residual_m",
        "state timeline": "nav_state",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.metric_combo = QComboBox()
        self.metric_combo.addItems(self.METRICS.keys())

        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self._rows: list[dict[str, object]] = []

        self.metric_combo.currentTextChanged.connect(self._redraw)

        layout = QVBoxLayout()
        layout.addWidget(self.metric_combo)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def set_data(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows
        self._redraw()

    def clear(self) -> None:
        self._rows = []
        self._redraw()

    def _redraw(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not self._rows:
            ax.set_title("No replay data")
            self.canvas.draw_idle()
            return

        x_values = [float(row.get("t_sec", 0.0) or 0.0) for row in self._rows]
        metric_name = self.metric_combo.currentText()
        key = self.METRICS[metric_name]

        if key == "nav_state":
            ordered_states = ["unknown", "good", "degraded", "recovering", "invalid"]

            def _normalize_state(value: object) -> str:
                raw = str(value or "unknown").strip()
                if "." in raw:
                    raw = raw.split(".")[-1]
                raw = raw.lower()
                if raw not in ordered_states:
                    raw = "unknown"
                return raw

            y_values = [
                ordered_states.index(_normalize_state(row.get("nav_state", "unknown")))
                for row in self._rows
            ]
            ax.plot(x_values, y_values, linewidth=1.5)
            ax.set_yticks(list(range(len(ordered_states))), [s.upper() for s in ordered_states])

        else:
            y_values = [float(row.get(key, 0.0) or 0.0) for row in self._rows]
            ax.plot(x_values, y_values, linewidth=1.5)

        ax.set_xlabel("t_sec")
        ax.set_ylabel(metric_name)
        ax.grid(True, alpha=0.3)
        ax.set_title(metric_name)
        self.canvas.draw_idle()
