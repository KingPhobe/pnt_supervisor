"""Helpers for serializing replay epoch rows."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.fusion.evidence_fuser import FusedEvidence
from pnt_supervisor.fusion.state_machine import StateSnapshot


FEATURE_COLUMNS = ["jump_distance_m", "gap_ratio", "state_flap_count"]


class DetectorResultLike(Protocol):
    detector_name: str
    score: float
    metrics: dict[str, Any]
    reason_codes: list[str]


def detector_scores_by_name(
    detector_results: Sequence[DetectorResultLike],
) -> dict[str, float]:
    return {result.detector_name: result.score for result in detector_results}


def metrics_for_detector(
    detector_results: Sequence[DetectorResultLike], detector_name: str
) -> dict[str, Any]:
    return next(
        (result.metrics for result in detector_results if result.detector_name == detector_name),
        {},
    )


def reason_text_for_detector(
    detector_results: Sequence[DetectorResultLike], detector_name: str
) -> str:
    return next(
        (
            "|".join(result.reason_codes)
            for result in detector_results
            if result.detector_name == detector_name and result.reason_codes
        ),
        "",
    )


def build_replay_epoch_row(
    *,
    obs: EpochObservation,
    feature_vector: FeatureVector,
    detector_results: Sequence[DetectorResultLike],
    fused: FusedEvidence,
    snapshot: StateSnapshot,
) -> dict[str, Any]:
    detector_scores = detector_scores_by_name(detector_results)
    speed_accel_metrics = metrics_for_detector(detector_results, "speed_accel_consistency")
    time_metrics = metrics_for_detector(detector_results, "time_consistency")
    speed_accel_reason = reason_text_for_detector(detector_results, "speed_accel_consistency")

    return {
        "t_sec": obs.t_sec,
        "source_name": obs.source_name,
        "fix_valid": obs.fix_valid,
        "num_sats": obs.num_sats,
        "hdop": obs.hdop,
        "msg_gap_s": obs.msg_gap_s,
        **{k: feature_vector.values.get(k, 0.0) for k in FEATURE_COLUMNS},
        **detector_scores,
        "gps_speed_mps": speed_accel_metrics.get("gps_speed_mps", obs.speed_mps),
        "gps_accel_mps2": speed_accel_metrics.get("gps_accel_mps2", 0.0),
        "imu_dynamic_accel_mps2": speed_accel_metrics.get("imu_dynamic_accel_mps2", 0.0),
        "residual_mps2": speed_accel_metrics.get("residual_mps2", 0.0),
        "ratio": speed_accel_metrics.get("ratio", 0.0),
        "warning_flag": int(speed_accel_metrics.get("warning_flag", 0.0)),
        "fault_flag": int(speed_accel_metrics.get("fault_flag", 0.0)),
        "health_score": speed_accel_metrics.get("health_score", 1.0),
        "reason": speed_accel_reason,
        "time_dt_gps_s": feature_vector.values.get("time_dt_gps_s", 0.0),
        "time_dt_log_s": feature_vector.values.get("time_dt_log_s", 0.0),
        "time_dt_mismatch_s": time_metrics.get(
            "time_dt_mismatch_s", feature_vector.values.get("time_dt_mismatch_s", 0.0)
        ),
        "time_clock_drift_ppm": time_metrics.get(
            "time_clock_drift_ppm", feature_vector.values.get("time_clock_drift_ppm", 0.0)
        ),
        "time_clock_fit_rms_s": time_metrics.get(
            "time_clock_fit_rms_s", feature_vector.values.get("time_clock_fit_rms_s", 0.0)
        ),
        "time_motion_residual_m": time_metrics.get(
            "time_motion_residual_m", feature_vector.values.get("time_motion_residual_m", 0.0)
        ),
        "time_implied_residual_s": time_metrics.get(
            "time_implied_residual_s", feature_vector.values.get("time_implied_residual_s", 0.0)
        ),
        "detector_time_consistency_score": detector_scores.get("time_consistency", 0.0),
        "fused_score": fused.nav_score,
        "nav_state": snapshot.state.value,
        "reasons": "|".join(fused.reasons),
    }
