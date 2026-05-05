from pnt_supervisor.core import FeatureFlag, FeatureValue


def test_feature_flag_constants() -> None:
    assert FeatureFlag.TIMESTAMP_BACKWARDS == "timestamp_backwards"
    assert FeatureFlag.HOVER_VALID == "hover_valid"


def test_feature_value_constants() -> None:
    assert FeatureValue.STALE_COUNT == "stale_count"
    assert FeatureValue.FD_SPEED_MPS == "fd_speed_mps"
