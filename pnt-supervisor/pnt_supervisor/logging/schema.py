"""CSV-friendly row schema helpers for supervisor step results."""

from collections.abc import Mapping
from typing import Any

from pnt_supervisor.supervisor.pipeline import SupervisorStepResult


DEFAULT_EPOCH_COLUMNS: tuple[str, ...] = (
    "t_sec",
    "source_name",
    "lat_deg",
    "lon_deg",
    "alt_m",
    "fix_valid",
    "num_sats",
    "hdop",
    "nav_state",
    "nav_score",
    "hard_fail_active",
    "reasons",
    "jump_distance_m",
    "fd_speed_mps",
    "speed_mismatch_mps",
    "course_track_mismatch_deg",
    "stale_count",
    "state_flap_count",
)


def _feature_value(values: Mapping[str, Any], key: str) -> Any:
    return values.get(key, "")


def supervisor_step_to_row(result: SupervisorStepResult) -> dict[str, Any]:
    obs = result.observation
    features = result.features
    decision = result.decision

    row: dict[str, Any] = {
        "t_sec": obs.t_sec,
        "source_name": obs.source_name,
        "lat_deg": obs.lat_deg,
        "lon_deg": obs.lon_deg,
        "alt_m": obs.alt_m,
        "fix_valid": obs.fix_valid,
        "num_sats": obs.num_sats,
        "hdop": obs.hdop,
        "nav_state": decision.nav_state.value,
        "nav_score": decision.nav_score,
        "hard_fail_active": decision.hard_fail_active,
        "reasons": ";".join(decision.reasons),
    }

    for key in DEFAULT_EPOCH_COLUMNS:
        if key not in row:
            row[key] = _feature_value(features.values, key)

    return row
