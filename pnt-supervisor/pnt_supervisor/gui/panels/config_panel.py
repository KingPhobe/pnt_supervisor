"""Editable numeric thresholds with JSON save/load support."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pnt_supervisor.core.config import AppConfig


class ConfigPanel(QWidget):
    """Panel for editing and persisting AppConfig numeric values."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._fields: dict[str, QDoubleSpinBox] = {}

        form = QFormLayout()
        self._add_field(form, "thresholds.max_msg_gap_s", "Max message gap (s)")
        self._add_field(form, "thresholds.max_hdop", "Max HDOP")
        self._add_field(form, "thresholds.max_vdop", "Max VDOP")
        self._add_field(form, "thresholds.max_hacc_m", "Max HACC (m)")
        self._add_field(form, "thresholds.max_vacc_m", "Max VACC (m)")
        self._add_field(form, "thresholds.hard_fail_score", "Hard fail score")
        self._add_field(form, "fusion.score_decay_per_s", "Score decay/s")
        self._add_field(form, "fusion.hard_fail_hold_s", "Hard fail hold (s)")
        self._add_field(form, "fusion.recovering_threshold", "Recovering threshold")
        self._add_field(form, "fusion.good_threshold", "Good threshold")

        save_button = QPushButton("Save JSON")
        load_button = QPushButton("Load JSON")
        save_button.clicked.connect(self.save_json)
        load_button.clicked.connect(self.load_json)

        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(load_button)
        button_layout.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(button_layout)
        layout.addStretch(1)
        self.setLayout(layout)

        self.set_config(AppConfig())

    def _add_field(self, layout: QFormLayout, path: str, label: str) -> None:
        spin = QDoubleSpinBox()
        spin.setRange(-1e6, 1e6)
        spin.setDecimals(6)
        self._fields[path] = spin
        layout.addRow(label + ":", spin)

    def set_config(self, config: AppConfig) -> None:
        data = config.model_dump()
        for path, spin in self._fields.items():
            top, key = path.split(".", 1)
            value = float(data[top][key])
            spin.setValue(value)

    def get_config(self) -> AppConfig:
        data = AppConfig().model_dump()
        for path, spin in self._fields.items():
            top, key = path.split(".", 1)
            data[top][key] = float(spin.value())
        return AppConfig.model_validate(data)

    def save_json(self) -> None:
        path_text, _ = QFileDialog.getSaveFileName(self, "Save config", "config.json", "JSON files (*.json)")
        if not path_text:
            return

        output_path = Path(path_text)
        payload = self.get_config().model_dump(mode="json")
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_json(self) -> None:
        path_text, _ = QFileDialog.getOpenFileName(self, "Load config", "", "JSON files (*.json)")
        if not path_text:
            return

        try:
            payload = json.loads(Path(path_text).read_text(encoding="utf-8"))
            config = AppConfig.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Invalid config", str(exc))
            return

        self.set_config(config)
