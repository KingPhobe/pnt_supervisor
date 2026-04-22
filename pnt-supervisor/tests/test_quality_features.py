from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.features.quality import QualityFeatureExtractor


def test_large_hdop_sets_geometry_bad() -> None:
    extractor = QualityFeatureExtractor(hdop_bad_threshold=6.0)
    obs = EpochObservation(t_sec=1.0, fix_valid=True, hdop=99.0, num_sats=8)

    out = extractor.extract(obs, FeatureVector())

    assert out.flags["hdop_bad"] is True
    assert out.flags["geometry_bad"] is True


def test_fix_transition_count_short_window_increments() -> None:
    extractor = QualityFeatureExtractor(transition_window=10)
    for i, valid in enumerate([True, True, False, False, True]):
        out = extractor.extract(EpochObservation(t_sec=float(i), fix_valid=valid), FeatureVector())

    assert out.values["fix_transition_count_short_window"] == 2.0
