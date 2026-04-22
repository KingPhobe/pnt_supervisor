"""Replay input controls: source type, replay file path, and run/reset actions."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class InputPanel(QWidget):
    """Input panel for selecting replay source and launching analysis."""

    run_requested = pyqtSignal(str, str)
    reset_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.nmea_radio = QRadioButton("NMEA file")
        self.xlsx_radio = QRadioButton("XLSX file")
        self.nmea_radio.setChecked(True)

        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Select replay file...")

        browse_button = QPushButton("Browse")
        run_button = QPushButton("Run")
        reset_button = QPushButton("Reset")

        browse_button.clicked.connect(self._browse_file)
        run_button.clicked.connect(self._emit_run)
        reset_button.clicked.connect(self.reset_requested.emit)

        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source type:"))
        source_layout.addWidget(self.nmea_radio)
        source_layout.addWidget(self.xlsx_radio)
        source_layout.addStretch(1)

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(browse_button)

        action_layout = QHBoxLayout()
        action_layout.addWidget(run_button)
        action_layout.addWidget(reset_button)
        action_layout.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(source_layout)
        layout.addLayout(file_layout)
        layout.addLayout(action_layout)
        layout.addStretch(1)
        self.setLayout(layout)

    def _selected_source_type(self) -> str:
        return "xlsx" if self.xlsx_radio.isChecked() else "nmea"

    def _browse_file(self) -> None:
        source_type = self._selected_source_type()
        if source_type == "xlsx":
            filter_text = "Excel files (*.xlsx)"
        else:
            filter_text = "NMEA files (*.txt *.log *.nmea)"

        selected, _ = QFileDialog.getOpenFileName(self, "Select replay file", "", filter_text)
        if selected:
            self.file_edit.setText(selected)

    def _emit_run(self) -> None:
        source_type = self._selected_source_type()
        path_text = self.file_edit.text().strip()
        if not path_text:
            QMessageBox.warning(self, "Missing file", "Please choose a replay file.")
            return

        path = Path(path_text)
        if not path.exists():
            QMessageBox.warning(self, "Invalid file", f"File does not exist:\n{path}")
            return

        self.run_requested.emit(source_type, str(path))
