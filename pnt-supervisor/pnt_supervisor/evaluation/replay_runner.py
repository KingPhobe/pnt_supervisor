"""Offline replay runner wiring adapter -> features -> detectors -> fusion -> state machine."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pnt_supervisor.adapters.base import ObservationAdapter
from pnt_supervisor.core.enums import NavState
from pnt_supervisor.core.models import FeatureVector
from pnt_supervisor.detectors import (
    HardGatesDetector,
    KinematicAnomalyDetector,
    ModeFlapDetector,
    StaleDataDetector,
    StatisticalDetector,
)
from pnt_supervisor.exports import TransitionEvent
from pnt_supervisor.features import (
    KinematicFeatureExtractor,
    QualityFeatureExtractor,
    RecoveryFeatureExtractor,
    TimingFeatureExtractor,
)
from pnt_supervisor.fusion.evidence_fuser import EvidenceFuser
from pnt_supervisor.fusion.state_machine import SupervisorStateMachine

from .report_writer import ReplayReportWriter


FEATURE_COLUMNS = ["jump_distance_m", "gap_ratio", "state_flap_count"]


@dataclass(slots=True)
class ReplayRunResult:
    epoch_rows: list[dict[str, Any]]
    event_rows: list[dict[str, Any]]
    summary: dict[str, Any]
    output_paths: dict[str, Path]


class ReplayRunner:
    """Runs an adapter through the full supervisor pipeline and exports reports."""

    def __init__(
        self,
        adapter: ObservationAdapter,
        *,
        config: Any | None = None,
        feature_extractors: list[Any] | None = None,
        detectors: list[Any] | None = None,
        fuser: EvidenceFuser | None = None,
        state_machine: SupervisorStateMachine | None = None,
        report_writer: ReplayReportWriter | None = None,
    ) -> None:
        self.adapter = adapter
        self.config = config
        self.feature_extractors = feature_extractors or [
            KinematicFeatureExtractor(),
            TimingFeatureExtractor(),
            QualityFeatureExtractor(),
            RecoveryFeatureExtractor(),
        ]
        self.detectors = detectors or [
            HardGatesDetector(),
            KinematicAnomalyDetector(),
            StaleDataDetector(),
            ModeFlapDetector(),
            StatisticalDetector(),
        ]
        self.fuser = fuser or EvidenceFuser(config)
        self.state_machine = state_machine or SupervisorStateMachine(config)
        self.report_writer = report_writer or ReplayReportWriter()

    def run(self, output_dir: Path) -> ReplayRunResult:
        self.adapter.reset()

        epoch_rows: list[dict[str, Any]] = []
        transition_events: list[TransitionEvent] = []
        reason_histogram: Counter[str] = Counter()
        dwell_times: Counter[str] = Counter()

        previous_state = self.state_machine.current_state
        previous_t_sec: float | None = None

        invalid_events = 0
        degraded_events = 0

        for obs in self.adapter.iter_observations():
            feature_vector = FeatureVector(t_sec=obs.t_sec)
            for extractor in self.feature_extractors:
                feature_vector = extractor.extract(obs, feature_vector)

            detector_results = [det.evaluate(obs, feature_vector, self.config) for det in self.detectors]
            fused = self.fuser.fuse(detector_results)
            snapshot = self.state_machine.update(
                t_sec=obs.t_sec,
                nav_score=fused.nav_score,
                hard_fail_active=fused.hard_fail_active,
            )

            if previous_t_sec is not None:
                dwell_times[previous_state.value] += max(0.0, obs.t_sec - previous_t_sec)
            previous_t_sec = obs.t_sec

            if snapshot.state != previous_state:
                transition_events.append(
                    TransitionEvent(
                        t_sec=obs.t_sec,
                        from_state=previous_state.value,
                        to_state=snapshot.state.value,
                        reason=snapshot.last_transition_reason,
                    )
                )
                if snapshot.state == NavState.INVALID:
                    invalid_events += 1
                if snapshot.state == NavState.DEGRADED:
                    degraded_events += 1

            for reason in fused.reasons:
                reason_histogram[reason] += 1

            detector_scores = {result.detector_name: result.score for result in detector_results}
            epoch_rows.append(
                {
                    "t_sec": obs.t_sec,
                    "source_name": obs.source_name,
                    "fix_valid": obs.fix_valid,
                    "num_sats": obs.num_sats,
                    "hdop": obs.hdop,
                    "msg_gap_s": obs.msg_gap_s,
                    **{k: feature_vector.values.get(k, 0.0) for k in FEATURE_COLUMNS},
                    **detector_scores,
                    "fused_score": fused.nav_score,
                    "nav_state": snapshot.state.value,
                    "reasons": "|".join(fused.reasons),
                }
            )
            previous_state = snapshot.state

        if previous_t_sec is not None:
            dwell_times[previous_state.value] += 0.0

        event_rows = [event.to_row() for event in transition_events]
        summary = {
            "total_epochs": len(epoch_rows),
            "state_dwell_times_s": {state: float(value) for state, value in dwell_times.items()},
            "invalid_events": invalid_events,
            "degraded_events": degraded_events,
            "reason_histogram": dict(reason_histogram),
        }

        output_paths = self.report_writer.write(
            output_dir,
            epoch_rows=epoch_rows,
            event_rows=event_rows,
            summary=summary,
        )

        return ReplayRunResult(
            epoch_rows=epoch_rows,
            event_rows=event_rows,
            summary=summary,
            output_paths=output_paths,
        )
