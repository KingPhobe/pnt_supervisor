from types import SimpleNamespace

from pnt_supervisor.core.models import DetectorResult
from pnt_supervisor.fusion.evidence_fuser import EvidenceFuser


def test_fuser_combines_weighted_health_and_reasons() -> None:
    cfg = SimpleNamespace(
        fusion=SimpleNamespace(
            detector_weights={
                "stale_data": 0.2,
                "kinematic_anomaly": 0.3,
                "mode_flap": 0.1,
                "statistical": 0.4,
            }
        )
    )
    fuser = EvidenceFuser(cfg)

    results = [
        DetectorResult(detector_name="stale_data", score=0.20, reason_codes=["STALE"]),
        DetectorResult(detector_name="kinematic_anomaly", score=0.50, reason_codes=["KIN"]),
        DetectorResult(detector_name="mode_flap", score=0.00, reason_codes=[]),
        DetectorResult(detector_name="statistical", score=0.25, reason_codes=["KIN", "STAT"]),
    ]

    fused = fuser.fuse(results)

    assert fused.hard_fail_active is False
    assert fused.reasons == ["STALE", "KIN", "STAT"]
    # health = sum((1-score)*weight) / sum(weight)
    expected = (0.8 * 0.2 + 0.5 * 0.3 + 1.0 * 0.1 + 0.75 * 0.4) / 1.0
    assert fused.nav_score == expected


def test_fuser_hard_fail_forces_untrusted_score() -> None:
    fuser = EvidenceFuser()
    results = [
        DetectorResult(detector_name="stale_data", score=0.0),
        DetectorResult(detector_name="hard_gates", score=1.0, hard_fail=True, reason_codes=["IMPOSSIBLE_JUMP"]),
    ]

    fused = fuser.fuse(results)

    assert fused.hard_fail_active is True
    assert fused.nav_score == 0.0
    assert fused.reasons == ["IMPOSSIBLE_JUMP"]
