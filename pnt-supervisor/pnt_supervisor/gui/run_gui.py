"""Entry point for launching the replay-mode PyQt6 GUI."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from pnt_supervisor.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
