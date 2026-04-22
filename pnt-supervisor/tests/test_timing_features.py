from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.features.timing import TimingFeatureExtractor


def _obs(t: float, lat: float = 37.0, lon: float = -122.0, alt: float = 10.0) -> EpochObservation:
    return EpochObservation(t_sec=t, lat_deg=lat, lon_deg=lon, alt_m=alt, fix_valid=True)


def test_frozen_identical_positions_increment_frozen_solution_count() -> None:
    extractor = TimingFeatureExtractor()

    out1 = extractor.extract(_obs(0.0), FeatureVector())
    out2 = extractor.extract(_obs(1.0), FeatureVector())
    out3 = extractor.extract(_obs(2.0), FeatureVector())

    assert out1.values["frozen_solution_count"] == 0.0
    assert out2.values["frozen_solution_count"] == 1.0
    assert out3.values["frozen_solution_count"] == 2.0


def test_timestamp_backwards_flagged() -> None:
    extractor = TimingFeatureExtractor()
    extractor.extract(_obs(5.0), FeatureVector())
    out = extractor.extract(_obs(4.0), FeatureVector())

    assert out.flags["timestamp_backwards"] is True
