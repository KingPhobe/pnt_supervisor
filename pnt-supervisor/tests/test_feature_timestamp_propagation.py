from pnt_supervisor.core.models import EpochObservation, FeatureVector
from pnt_supervisor.features.kinematics import KinematicFeatureExtractor
from pnt_supervisor.features.quality import QualityFeatureExtractor
from pnt_supervisor.features.recovery import RecoveryFeatureExtractor
from pnt_supervisor.features.timing import TimingFeatureExtractor


def test_extractors_set_output_timestamp_from_observation() -> None:
    obs = EpochObservation(t_sec=123.5, lat_deg=37.0, lon_deg=-122.0, fix_valid=True)

    extractors = [
        TimingFeatureExtractor(),
        QualityFeatureExtractor(),
        KinematicFeatureExtractor(),
        RecoveryFeatureExtractor(),
    ]

    for extractor in extractors:
        out = extractor.extract(obs, FeatureVector())
        assert out.t_sec == 123.5
