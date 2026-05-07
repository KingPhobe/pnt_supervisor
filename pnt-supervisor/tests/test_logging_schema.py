import builtins
import importlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from pnt_supervisor.core import NavState
from pnt_supervisor.core.models import EpochObservation, FeatureVector, SupervisorDecision
from pnt_supervisor.supervisor import SupervisorStepResult


@contextmanager
def _block_pandas_imports() -> Iterator[None]:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "pandas" or name.startswith("pandas."):
            raise AssertionError("pandas should not be imported by logging schema")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = guarded_import
    try:
        yield
    finally:
        builtins.__import__ = original_import


def _step_result(
    *,
    reasons: list[str] | None = None,
    features: dict[str, float] | None = None,
    nav_state: NavState = NavState.DEGRADED,
) -> SupervisorStepResult:
    return SupervisorStepResult(
        observation=EpochObservation(
            t_sec=12.5,
            source_name="gps0",
            lat_deg=37.1,
            lon_deg=-122.2,
            alt_m=42.0,
            fix_valid=True,
            num_sats=10,
            hdop=0.8,
        ),
        features=FeatureVector(values=features or {}),
        decision=SupervisorDecision(
            nav_state=nav_state,
            nav_score=0.4,
            reasons=reasons or [],
            hard_fail_active=True,
        ),
    )


def test_supervisor_step_to_row_returns_all_default_epoch_columns() -> None:
    from pnt_supervisor.logging import DEFAULT_EPOCH_COLUMNS, supervisor_step_to_row

    row = supervisor_step_to_row(
        _step_result(
            features={
                "jump_distance_m": 1.2,
                "fd_speed_mps": 3.4,
                "speed_mismatch_mps": 5.6,
                "course_track_mismatch_deg": 7.8,
                "stale_count": 2.0,
                "state_flap_count": 3.0,
            }
        )
    )

    assert tuple(row) == DEFAULT_EPOCH_COLUMNS
    assert set(DEFAULT_EPOCH_COLUMNS) <= row.keys()


def test_nav_state_is_serialized_as_enum_value_string() -> None:
    from pnt_supervisor.logging import supervisor_step_to_row

    row = supervisor_step_to_row(_step_result(nav_state=NavState.INVALID))

    assert row["nav_state"] == "invalid"


def test_reasons_list_is_serialized_with_semicolon_separator() -> None:
    from pnt_supervisor.logging import supervisor_step_to_row

    row = supervisor_step_to_row(_step_result(reasons=["low_sats", "high_hdop"]))

    assert row["reasons"] == "low_sats;high_hdop"


def test_missing_feature_values_become_empty_string() -> None:
    from pnt_supervisor.logging import supervisor_step_to_row

    row = supervisor_step_to_row(_step_result(features={"jump_distance_m": 9.0}))

    assert row["jump_distance_m"] == 9.0
    assert row["fd_speed_mps"] == ""
    assert row["speed_mismatch_mps"] == ""
    assert row["course_track_mismatch_deg"] == ""
    assert row["stale_count"] == ""
    assert row["state_flap_count"] == ""


def test_no_pandas_import_is_required() -> None:
    sys.modules.pop("pnt_supervisor.logging", None)
    sys.modules.pop("pnt_supervisor.logging.schema", None)

    with _block_pandas_imports():
        module = importlib.import_module("pnt_supervisor.logging")
        row = module.supervisor_step_to_row(_step_result())

    assert row["source_name"] == "gps0"
