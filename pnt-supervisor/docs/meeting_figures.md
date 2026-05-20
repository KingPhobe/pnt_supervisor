# Meeting Figures Utility

`tools/generate_meeting_figures.py` is a lightweight reporting helper for turning test/simulation CSV outputs into presentation-ready PNG plots. It is intentionally separate from supervisor decision logic so it can be used in analysis workflows without affecting runtime behavior.

## Usage

From the repository root (`pnt-supervisor/`):

```bash
python tools/generate_meeting_figures.py --csv path/to/results.csv --out-dir meeting_figures
```

Optional thresholds and title prefix:

```bash
python tools/generate_meeting_figures.py \
  --csv path/to/results.csv \
  --out-dir meeting_figures \
  --speed-threshold-mps 40.0 \
  --accel-threshold-mps2 15.0 \
  --min-movement-m 0.5 \
  --title-prefix "Demo Run"
```

The script creates `--out-dir` automatically if needed.

## Expected Columns (Alias-Based)

The script accepts multiple likely column names and picks the first match:

- Time: `t`, `time`, `time_s`, `timestamp`, `epoch_s`
- Position error: `position_error`, `position_error_m`, `pos_error`, `pos_error_m`, `horizontal_error_m`
- Speed: `speed`, `speed_mps`, `ground_speed`, `ground_speed_mps`
- Acceleration: `acceleration`, `accel`, `accel_mps2`, `acceleration_mps2`
- Movement: `movement`, `movement_m`, `displacement`, `displacement_m`, `window_displacement_m`
- Supervisor status: `supervisor_status`, `status`, `pnt_status`, `nav_status`
- Individual test flags: boolean/integer columns that start with `test_` or end with `_pass`, `_valid`, `_ok`

If specific columns are missing, the script prints warnings and continues generating whatever plots it can.

## Generated Plots

When data is available, these files are produced:

- `position_error.png`
- `speed_accel_thresholds.png`
- `movement_gate.png`
- `test_flags_timeline.png`
- `supervisor_status_timeline.png`

## Meeting Note: Quadcopter Bypass

In meeting slides, explain the quadcopter bypass as a **vehicle-profile-specific policy path** (for example, reduced hard-gating under known low-dynamics hover regimes), not as a suppression of safety checks. Emphasize that:

1. The bypass is intentional and scoped to the appropriate platform configuration.
2. Monitoring/telemetry still runs, so anomalies remain visible.
3. The plotted timelines (status + test flags + movement/speed/accel thresholds) provide evidence that the bypass behavior is understood and bounded.
