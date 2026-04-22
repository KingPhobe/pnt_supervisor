from types import SimpleNamespace

from pnt_supervisor.core.enums import FixType
from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.detectors.hard_gates import HardGatesDetector
from pnt_supervisor.detectors.kinematic_anomaly import KinematicAnomalyDetector
from pnt_supervisor.detectors.mode_flap import ModeFlapDetector
from pnt_supervisor.detectors.stale_data import StaleDataDetector
from pnt_supervisor.detectors.statistical import StatisticalDetector
from pnt_supervisor.features.kinematics import KinematicFeatureExtractor
from pnt_supervisor.features.quality import QualityFeatureExtractor
from pnt_supervisor.features.recovery import RecoveryFeatureExtractor
from pnt_supervisor.features.timing import TimingFeatureExtractor


CFG = SimpleNamespace(
    no_fix_timeout_s=5.0,
    stale_timeout_s=2.0,
    impossible_jump_m=150.0,
    frozen_solution_limit=5.0,
    extreme_hdop=10.0,
    max_speed_mps=25.0,
    max_turn_rate_dps=120.0,
    max_climb_mps=8.0,
    max_hdop=2.5,
)


def test_flapping_validity_raises_mode_flap_score() -> None:
    detector = ModeFlapDetector(window=20)
    recovery = RecoveryFeatureExtractor(flap_window=20)

    score = 0.0
    seq = [False, True, False, True, False, True]
    for i, valid in enumerate(seq):
        obs = EpochObservation(t_sec=float(i), fix_valid=valid, fix_type=FixType.FIX_3D)
        feat = recovery.extract(obs, FeatureVector())
        out = detector.evaluate(obs, feat, CFG)
        score = out.score

    assert score > 0.5


def test_healthy_short_sequence_keeps_scores_low() -> None:
    kin = KinematicFeatureExtractor()
    tim = TimingFeatureExtractor(expected_period_s=1.0, stale_threshold_s=2.0)
    qual = QualityFeatureExtractor(hdop_bad_threshold=6.0)
    rec = RecoveryFeatureExtractor(unstable_window_s=5.0)

    detectors = [
        HardGatesDetector(),
        KinematicAnomalyDetector(),
        StaleDataDetector(),
        ModeFlapDetector(),
        StatisticalDetector(),
    ]

    results = []
    for i in range(8):
        obs = EpochObservation(
            t_sec=float(i),
            lat_deg=37.0 + i * 0.000009,
            lon_deg=-122.0,
            alt_m=10.0,
            speed_mps=1.0,
            course_deg=0.0,
            climb_mps=0.0,
            fix_valid=True,
            fix_type=FixType.FIX_3D,
            hdop=0.9,
            msg_gap_s=1.0,
        )
        feat = FeatureVector(t_sec=obs.t_sec)
        for ex in (kin, tim, qual, rec):
            feat = ex.extract(obs, feat)
        results = [d.evaluate(obs, feat, CFG) for d in detectors]

    for result in results:
        assert 0.0 <= result.score <= 1.0
        if result.detector_name != "hard_gates":
            assert result.score < 0.4


def test_all_detector_scores_are_clamped() -> None:
    obs = EpochObservation(t_sec=1.0, fix_valid=False, fix_type=FixType.NO_FIX, hdop=200.0)
    feature = FeatureVector(
        values={
            "time_since_last_valid_fix_s": 99.0,
            "gap_s": 50.0,
            "gap_ratio": 500.0,
            "stale_count": 999.0,
            "frozen_solution_count": 999.0,
            "jump_distance_m": 999999.0,
            "speed_mismatch_mps": 999.0,
            "course_track_mismatch_deg": 999.0,
            "climb_mismatch_mps": 999.0,
            "hdop": 200.0,
        },
        flags={"timestamp_backwards": True, "reacq_unstable": True},
    )

    detectors = [
        HardGatesDetector(),
        KinematicAnomalyDetector(),
        StaleDataDetector(),
        ModeFlapDetector(),
        StatisticalDetector(),
    ]

    for detector in detectors:
        out = detector.evaluate(obs, feature, CFG)
        assert 0.0 <= out.score <= 1.0
