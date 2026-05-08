from pnt_supervisor.core.enums import NavState
from pnt_supervisor.core.models import DetectorResult, EpochObservation, FeatureVector
from pnt_supervisor.evaluation.replay_epoch_row import (
    build_replay_epoch_row,
    reason_text_for_detector,
)
from pnt_supervisor.fusion.evidence_fuser import FusedEvidence
from pnt_supervisor.fusion.state_machine import StateSnapshot


def _build_row() -> dict[str, object]:
    obs = EpochObservation(
        t_sec=12.5,
        source_name="synthetic",
        fix_valid=True,
        num_sats=9,
        hdop=0.8,
        msg_gap_s=1.1,
        speed_mps=4.2,
    )
    feature_vector = FeatureVector(
        t_sec=12.5,
        values={
            "jump_distance_m": 3.0,
            "gap_ratio": 1.5,
            "state_flap_count": 2.0,
            "time_dt_gps_s": 1.0,
            "time_dt_log_s": 1.2,
            "time_dt_mismatch_s": 0.2,
            "time_clock_drift_ppm": 9.0,
            "time_clock_fit_rms_s": 0.03,
            "time_motion_residual_m": 5.0,
            "time_implied_residual_s": 0.4,
        },
    )
    detector_results = [
        DetectorResult(detector_name="hard_gates", score=0.1),
        DetectorResult(
            detector_name="speed_accel_consistency",
            score=0.25,
            reason_codes=["ACCEL_WARN", "RESIDUAL_HIGH"],
            metrics={
                "gps_speed_mps": 4.5,
                "gps_accel_mps2": 0.7,
                "imu_dynamic_accel_mps2": 0.4,
                "residual_mps2": 0.3,
                "ratio": 1.75,
                "warning_flag": 1.0,
                "fault_flag": 0.0,
                "health_score": 0.75,
            },
        ),
        DetectorResult(
            detector_name="time_consistency",
            score=0.35,
            metrics={
                "time_dt_mismatch_s": 0.6,
                "time_clock_drift_ppm": 12.0,
                "time_clock_fit_rms_s": 0.08,
                "time_motion_residual_m": 6.0,
                "time_implied_residual_s": 0.9,
            },
        ),
    ]
    fused = FusedEvidence(nav_score=0.72, reasons=["ACCEL_WARN", "CLOCK_DRIFT"])
    snapshot = StateSnapshot(
        state=NavState.DEGRADED,
        time_in_state_s=3.0,
        last_transition_reason="below_degrade_threshold",
    )

    return build_replay_epoch_row(
        obs=obs,
        feature_vector=feature_vector,
        detector_results=detector_results,
        fused=fused,
        snapshot=snapshot,
    )


def test_build_replay_epoch_row_includes_core_observation_fields() -> None:
    row = _build_row()

    assert row["t_sec"] == 12.5
    assert row["source_name"] == "synthetic"
    assert row["fix_valid"] is True
    assert row["num_sats"] == 9
    assert row["hdop"] == 0.8
    assert row["msg_gap_s"] == 1.1
    assert row["jump_distance_m"] == 3.0
    assert row["gap_ratio"] == 1.5
    assert row["state_flap_count"] == 2.0


def test_detector_scores_are_included_using_detector_name_as_key() -> None:
    row = _build_row()

    assert row["hard_gates"] == 0.1
    assert row["speed_accel_consistency"] == 0.25
    assert row["time_consistency"] == 0.35
    assert row["detector_time_consistency_score"] == 0.35


def test_speed_accel_consistency_metrics_are_mapped_correctly() -> None:
    row = _build_row()

    assert row["gps_speed_mps"] == 4.5
    assert row["gps_accel_mps2"] == 0.7
    assert row["imu_dynamic_accel_mps2"] == 0.4
    assert row["residual_mps2"] == 0.3
    assert row["ratio"] == 1.75
    assert row["warning_flag"] == 1
    assert row["fault_flag"] == 0
    assert row["health_score"] == 0.75
    assert row["reason"] == "ACCEL_WARN|RESIDUAL_HIGH"


def test_time_consistency_metrics_are_mapped_correctly() -> None:
    row = _build_row()

    assert row["time_dt_gps_s"] == 1.0
    assert row["time_dt_log_s"] == 1.2
    assert row["time_dt_mismatch_s"] == 0.6
    assert row["time_clock_drift_ppm"] == 12.0
    assert row["time_clock_fit_rms_s"] == 0.08
    assert row["time_motion_residual_m"] == 6.0
    assert row["time_implied_residual_s"] == 0.9


def test_fused_score_nav_state_and_reasons_are_serialized_correctly() -> None:
    row = _build_row()

    assert row["fused_score"] == 0.72
    assert row["nav_state"] == "degraded"
    assert row["reasons"] == "ACCEL_WARN|CLOCK_DRIFT"


def test_reason_text_for_detector_joins_reason_codes_with_pipe() -> None:
    detector_results = [
        DetectorResult(detector_name="hard_gates", reason_codes=["HARD"]),
        DetectorResult(detector_name="target", reason_codes=["ONE", "TWO"]),
    ]

    assert reason_text_for_detector(detector_results, "target") == "ONE|TWO"
