# pnt-supervisor

Standalone Python package containing shared enums, core dataclasses, and
configuration objects for a Positioning, Navigation, and Timing (PNT)
supervisor pipeline.

## Requirements

- Python 3.11+

## Install (development)

```bash
python -m pip install -e ".[dev]"
```

## Run tests

```bash
pytest -q
```

## Platform-aware hover behavior

`KinematicFeatureExtractor` accepts `PlatformConfig` so near-zero movement can
be interpreted by platform type:

- Fixed-wing/default platforms mark near-zero motion as
  `low_motion_suspicious=True`.
- Quadcopter/hover-capable platforms (`PlatformConfig.quadcopter()`) mark the
  same condition as `hover_valid=True` and not suspicious.
- In both cases, near-zero displacement sets `track_geometry_ambiguous=True`
  and forces `course_track_mismatch_deg=0.0`, avoiding unstable bearing math.

## Decision engine

`DecisionEngine` combines feature flags and counters into final nav states:

- `INVALID` for hard-invalid timing flags (for example
  `timestamp_backwards`, `kinematic_time_invalid`).
- `RECOVERING` for `reacq_unstable`.
- `DEGRADED` for soft quality/kinematic issues and thresholds like
  `stale_count` / `state_flap_count`.
- `GOOD` otherwise.
