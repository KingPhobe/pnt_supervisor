"""Main replay-mode GUI window for PNT supervisor analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from pnt_supervisor.adapters import ArduPilotLogXLSXAdapter, NMEAReplayAdapter
from pnt_supervisor.evaluation.replay_runner import ReplayRunResult, ReplayRunner
from pnt_supervisor.gui.panels import (
    ConfigPanel,
    DecisionPanel,
    EventsPanel,
    FeaturesPanel,
    InputPanel,
    PlotsPanel,
)


class MainWindow(QMainWindow):
    """Tabbed replay-analysis GUI for loading files and inspecting outputs."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PNT Supervisor — Replay Analysis")
        self.resize(1100, 700)

        self.input_panel = InputPanel()
        self.features_panel = FeaturesPanel()
        self.decision_panel = DecisionPanel()
        self.events_panel = EventsPanel()
        self.plots_panel = PlotsPanel()
        self.config_panel = ConfigPanel()

        tabs = QTabWidget()
        tabs.addTab(self.input_panel, "Input")
        tabs.addTab(self.features_panel, "Features")
        tabs.addTab(self.decision_panel, "Decision")
        tabs.addTab(self.events_panel, "Events")
        tabs.addTab(self.plots_panel, "Plots")
        tabs.addTab(self.config_panel, "Config")
        self.setCentralWidget(tabs)

        self.input_panel.run_requested.connect(self._run_replay)
        self.input_panel.reset_requested.connect(self._reset_panels)
        self.statusBar().showMessage("Ready")

    def _run_replay(self, source_type: str, file_path: str) -> None:
        try:
            adapter = self._build_adapter(source_type, file_path)
            runner = ReplayRunner(adapter, config=self.config_panel.get_config())
            output_dir = Path(tempfile.mkdtemp(prefix="pnt_supervisor_gui_"))
            result = runner.run(output_dir)
            self._apply_result(result)
            self.statusBar().showMessage(f"Replay completed: {len(result.epoch_rows)} epochs")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Replay failed", str(exc))
            self.statusBar().showMessage("Replay failed")

    def _build_adapter(self, source_type: str, file_path: str):
        if source_type == "xlsx":
            return ArduPilotLogXLSXAdapter(file_path)
        return NMEAReplayAdapter(file_path)

    def _apply_result(self, result: ReplayRunResult) -> None:
        latest = result.epoch_rows[-1] if result.epoch_rows else None
        self.features_panel.update_features(latest)

        if latest:
            nav_state = str(latest.get("nav_state", "UNKNOWN"))
            fused_score = float(latest.get("fused_score", 0.0) or 0.0)
            reasons = str(latest.get("reasons", ""))
            time_in_state = self._current_state_duration(result.epoch_rows, nav_state)
            self.decision_panel.update_decision(nav_state, fused_score, reasons, time_in_state)
        else:
            self.decision_panel.clear()

        self.events_panel.set_events(result.event_rows)
        self.plots_panel.set_data(result.epoch_rows)

    @staticmethod
    def _current_state_duration(rows: list[dict[str, object]], current_state: str) -> float:
        if len(rows) < 2:
            return 0.0

        end_t = float(rows[-1].get("t_sec", 0.0) or 0.0)
        start_t = end_t
        for row in reversed(rows[:-1]):
            if str(row.get("nav_state", "")) != current_state:
                break
            start_t = float(row.get("t_sec", start_t) or start_t)
        return max(0.0, end_t - start_t)

    def _reset_panels(self) -> None:
        self.features_panel.clear()
        self.decision_panel.clear()
        self.events_panel.clear()
        self.plots_panel.clear()
        self.statusBar().showMessage("Reset")
