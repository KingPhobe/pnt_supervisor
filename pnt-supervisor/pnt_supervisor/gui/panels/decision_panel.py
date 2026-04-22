"""Panel showing current supervisory decision outputs."""

from __future__ import annotations

from PyQt6.QtWidgets import QFormLayout, QLabel, QWidget


class DecisionPanel(QWidget):
    """Displays state, score, reasons, and time in current state."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.current_state = QLabel("-")
        self.current_score = QLabel("-")
        self.active_reasons = QLabel("-")
        self.time_in_state = QLabel("-")

        layout = QFormLayout()
        layout.addRow("Current state:", self.current_state)
        layout.addRow("Current score:", self.current_score)
        layout.addRow("Active reasons:", self.active_reasons)
        layout.addRow("Time in state (s):", self.time_in_state)
        self.setLayout(layout)

    def update_decision(self, state: str, score: float, reasons: str, time_in_state_s: float) -> None:
        self.current_state.setText(state)
        self.current_score.setText(f"{score:.3f}")
        self.active_reasons.setText(reasons or "-")
        self.time_in_state.setText(f"{time_in_state_s:.2f}")

    def clear(self) -> None:
        self.current_state.setText("-")
        self.current_score.setText("-")
        self.active_reasons.setText("-")
        self.time_in_state.setText("-")
