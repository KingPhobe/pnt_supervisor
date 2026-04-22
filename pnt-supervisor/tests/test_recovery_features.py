from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.features.recovery import RecoveryFeatureExtractor


def test_invalid_valid_invalid_toggling_increments_state_flap_count() -> None:
    extractor = RecoveryFeatureExtractor(flap_window=10)

    sequence = [False, True, False]
    for i, valid in enumerate(sequence):
        out = extractor.extract(EpochObservation(t_sec=float(i), fix_valid=valid), FeatureVector())

    assert out.values["state_flap_count"] == 2.0


def test_recent_reacquisition_marked_unstable() -> None:
    extractor = RecoveryFeatureExtractor(unstable_window_s=5.0)
    extractor.extract(EpochObservation(t_sec=0.0, fix_valid=False), FeatureVector())
    out = extractor.extract(EpochObservation(t_sec=2.0, fix_valid=True), FeatureVector())

    assert out.flags["reacq_unstable"] is True
    assert out.values["time_since_last_invalid"] == 2.0
