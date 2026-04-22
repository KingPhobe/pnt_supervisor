"""Panel showing transition-history events."""

from __future__ import annotations

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class EventsPanel(QWidget):
    """Simple table of transition events from replay output."""

    COLUMNS = ["t_sec", "from_state", "to_state", "reason"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def set_events(self, rows: list[dict[str, object]]) -> None:
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, key in enumerate(self.COLUMNS):
                value = row.get(key, "")
                if key == "t_sec":
                    try:
                        text = f"{float(value):.3f}"
                    except (TypeError, ValueError):
                        text = ""
                else:
                    text = str(value)
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(text))

    def clear(self) -> None:
        self.table.setRowCount(0)
