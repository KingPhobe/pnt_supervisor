from pnt_supervisor.core import EpochObservation, FeatureFlag, FeatureValue, NavState, PlatformConfig
from pnt_supervisor.features import FeaturePipeline
from pnt_supervisor.supervisor import SupervisorPipeline


def _obs(
    t_sec: float,
    *,
    lat_deg: float = 37.0,
    lon_deg: float = -122.0,
    alt_m: float = 10.0,
    speed_mps: float = 2.0,
    fix_valid: bool = True,
    hdop: float = 1.0,
    num_sats: int = 8,
) -> EpochObservation:
    return EpochObservation(
        t_sec=t_sec,
        lat_deg=lat_deg,
        lon_deg=lon_deg,
        alt_m=alt_m,
        speed_mps=speed_mps,
        fix_valid=fix_valid,
        hdop=hdop,
        num_sats=num_sats,
    )


def test_supervisor_sequence_good_degraded_invalid_recovering() -> None:
    supervisor = SupervisorPipeline()

    epoch0 = supervisor.step(
        _obs(
            0.0,
            lat_deg=37.0,
            lon_deg=-122.0,
            alt_m=10.0,
            fix_valid=True,
            hdop=1.0,
            num_sats=8,
        )
    )
    assert epoch0.decision.nav_state is not NavState.INVALID

    epoch1 = supervisor.step(
        _obs(
            1.0,
            lat_deg=37.00002,
            lon_deg=-122.0,
            alt_m=10.0,
            speed_mps=2.0,
            fix_valid=True,
            hdop=1.0,
            num_sats=8,
        )
    )
    assert epoch1.decision.nav_state is not NavState.INVALID

    epoch2 = supervisor.step(
        _obs(
            2.0,
            lat_deg=37.00002,
            lon_deg=-122.0,
            alt_m=10.0,
            speed_mps=2.0,
            fix_valid=True,
            hdop=99.0,
            num_sats=8,
        )
    )
    assert epoch2.decision.nav_state is NavState.DEGRADED
    assert epoch2.features.flags[FeatureFlag.HDOP_BAD] is True
    assert epoch2.features.flags[FeatureFlag.GEOMETRY_BAD] is True

    epoch3 = supervisor.step(
        _obs(
            1.5,
            lat_deg=37.00002,
            lon_deg=-122.0,
            alt_m=10.0,
            speed_mps=2.0,
            fix_valid=True,
            hdop=1.0,
            num_sats=8,
        )
    )
    assert epoch3.decision.nav_state is NavState.INVALID
    assert epoch3.features.flags[FeatureFlag.TIMESTAMP_BACKWARDS] is True

    epoch4 = supervisor.step(
        _obs(
            4.0,
            lat_deg=37.00002,
            lon_deg=-122.0,
            alt_m=10.0,
            speed_mps=2.0,
            fix_valid=False,
            hdop=1.0,
            num_sats=8,
        )
    )
    assert epoch4.features.values[FeatureValue.FIX_VALID_NUMERIC] == 0.0

    epoch5 = supervisor.step(
        _obs(
            5.0,
            lat_deg=37.00002,
            lon_deg=-122.0,
            alt_m=10.0,
            speed_mps=2.0,
            fix_valid=True,
            hdop=1.0,
            num_sats=8,
        )
    )
    assert epoch5.decision.nav_state is NavState.RECOVERING
    assert epoch5.features.flags[FeatureFlag.REACQ_UNSTABLE] is True


def test_quadcopter_hover_full_pipeline_stays_good() -> None:
    feature_pipeline = FeaturePipeline.default(platform_config=PlatformConfig.quadcopter())
    supervisor = SupervisorPipeline(feature_pipeline=feature_pipeline)

    supervisor.step(
        _obs(
            0.0,
            lat_deg=37.0,
            lon_deg=-122.0,
            speed_mps=0.0,
            fix_valid=True,
            hdop=1.0,
            num_sats=8,
        )
    )
    result = supervisor.step(
        _obs(
            1.0,
            lat_deg=37.0,
            lon_deg=-122.0,
            speed_mps=0.0,
            fix_valid=True,
            hdop=1.0,
            num_sats=8,
        )
    )

    assert result.decision.nav_state is NavState.GOOD
    assert result.features.flags[FeatureFlag.HOVER_VALID] is True
    assert result.features.flags[FeatureFlag.LOW_MOTION_SUSPICIOUS] is False
