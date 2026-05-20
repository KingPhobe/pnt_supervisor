#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

TIME_ALIASES = ["t", "time", "time_s", "timestamp", "epoch_s", "t_sec"]
POSITION_ERROR_ALIASES = ["position_error", "position_error_m", "pos_error", "pos_error_m", "horizontal_error_m"]
SPEED_ALIASES = ["speed", "speed_mps", "ground_speed", "ground_speed_mps", "gps_speed_mps"]
ACCEL_ALIASES = ["acceleration", "accel", "accel_mps2", "acceleration_mps2", "gps_accel_mps2"]
MOVEMENT_ALIASES = ["movement", "movement_m", "displacement", "displacement_m", "window_displacement_m", "jump_distance_m"]
STATUS_ALIASES = ["supervisor_status", "status", "pnt_status", "nav_status", "nav_state"]
FUSED_SCORE_ALIASES = ["fused_score", "nav_score", "supervisor_score"]
HDOP_ALIASES = ["hdop", "HDOP", "gps_hdop"]
NUM_SATS_ALIASES = ["num_sats", "nsats", "satellites", "satellites_used", "GPS_0_NSats"]
FIX_VALID_ALIASES = ["fix_valid", "gps_fix_valid", "valid_fix"]


def find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lower_to_actual = {col.lower(): col for col in df.columns}
    for alias in aliases:
        if alias.lower() in lower_to_actual:
            return lower_to_actual[alias.lower()]
    return None


def add_relative_time_column(df: pd.DataFrame, t_col: str, units: str) -> tuple[str, str]:
    numeric_t = pd.to_numeric(df[t_col], errors="coerce")
    finite = numeric_t[pd.notna(numeric_t)]
    start = float(finite.iloc[0]) if not finite.empty else 0.0
    rel = numeric_t - start
    if units == "min":
        rel = rel / 60.0
    df["__time_rel__"] = rel
    return "__time_rel__", f"Time since start ({units})"


def find_test_flag_columns(df: pd.DataFrame) -> list[str]:
    exclude = set(TIME_ALIASES + POSITION_ERROR_ALIASES + SPEED_ALIASES + ACCEL_ALIASES + MOVEMENT_ALIASES + FUSED_SCORE_ALIASES + HDOP_ALIASES + NUM_SATS_ALIASES + STATUS_ALIASES)
    flag_cols: list[str] = []
    for col in df.columns:
        norm = col.lower()
        is_candidate = (
            norm.startswith("test_")
            or norm.endswith("_pass")
            or norm.endswith("_valid")
            or norm.endswith("_ok")
            or norm in {"fix_valid", "warning_flag", "fault_flag"}
        )
        if not is_candidate or norm in exclude:
            continue
        s = df[col]
        if pd.api.types.is_bool_dtype(s) or pd.api.types.is_integer_dtype(s):
            flag_cols.append(col)
    return flag_cols


def plot_position_error(df, x_col, x_label, out_dir, title_prefix):
    col = find_column(df, POSITION_ERROR_ALIASES)
    if col is None:
        print("Warning: cannot generate position_error.png; missing position error column.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df[x_col], df[col])
    ax.set_xlabel(x_label)
    ax.set_ylabel("Position Error (m)")
    ax.set_title(f"{title_prefix + ' - ' if title_prefix else ''}Position Error vs Time")
    ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(out_dir / "position_error.png", dpi=150); plt.close(fig)
    return True


def plot_speed_accel(df, x_col, x_label, speed_col, accel_col, out_dir, args):
    if speed_col is None and accel_col is None:
        print("Warning: cannot generate speed_accel_thresholds.png; missing speed and acceleration columns.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4))
    ax2 = None
    if speed_col is not None:
        ax.plot(df[x_col], df[speed_col], color="tab:blue", label="GPS speed")
        ax.axhline(args.speed_threshold_mps, linestyle="--", color="tab:blue", alpha=0.7, label=f"speed threshold ({args.speed_threshold_mps} m/s)")
        ax.set_ylabel("GPS speed (m/s)", color="tab:blue")
        ax.tick_params(axis="y", labelcolor="tab:blue")
    if accel_col is not None:
        if speed_col is not None:
            ax2 = ax.twinx()
            ax2.plot(df[x_col], df[accel_col], color="tab:orange", label="GPS acceleration")
            ax2.axhline(args.accel_threshold_mps2, linestyle=":", color="tab:orange", alpha=0.7, label=f"accel threshold ({args.accel_threshold_mps2} m/s²)")
            ax2.set_ylabel("GPS acceleration (m/s²)", color="tab:orange")
            ax2.tick_params(axis="y", labelcolor="tab:orange")
        else:
            ax.plot(df[x_col], df[accel_col], color="tab:orange", label="GPS acceleration")
            ax.axhline(args.accel_threshold_mps2, linestyle=":", color="tab:orange", alpha=0.7, label=f"accel threshold ({args.accel_threshold_mps2} m/s²)")
            ax.set_ylabel("GPS acceleration (m/s²)")
    ax.set_xlabel(x_label)
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Speed and Acceleration Thresholds")
    ax.grid(True, alpha=0.3)
    lines, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        l2, lb2 = ax2.get_legend_handles_labels(); lines += l2; labels += lb2
    ax.legend(lines, labels, loc="best")
    fig.tight_layout(); fig.savefig(out_dir / "speed_accel_thresholds.png", dpi=150); plt.close(fig)
    return True


def plot_movement_gate(df, x_col, x_label, movement_col, out_dir, args):
    if movement_col is None:
        print("Warning: cannot generate movement_gate.png; missing movement column.")
        return False
    movement = pd.to_numeric(df[movement_col], errors="coerce")
    clip_active = movement_col.lower() == "jump_distance_m" or movement.max(skipna=True) > args.clip_movement_m
    display = movement.clip(upper=args.clip_movement_m) if clip_active else movement
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df[x_col], display, label=movement_col)
    ax.axhline(args.min_movement_m, linestyle="--", label=f"min movement ({args.min_movement_m} m)")
    ax.set_xlabel(x_label); ax.set_ylabel("Movement / jump distance (m)")
    suffix = f" (clipped at {args.clip_movement_m:g} m)" if clip_active else ""
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Movement Gate{suffix}")
    if clip_active:
        ax.text(0.01, 0.98, "Large GNSS jumps are clipped for readability", transform=ax.transAxes, va="top", fontsize=9)
    ax.grid(True, alpha=0.3); ax.legend(); fig.tight_layout(); fig.savefig(out_dir / "movement_gate.png", dpi=150); plt.close(fig)
    return True


def plot_test_flags(df, x_col, x_label, flag_cols, out_dir, title_prefix):
    if not flag_cols:
        print("Warning: cannot generate test_flags_timeline.png; no matching test flag columns found.")
        return False
    fig_h = max(3, min(20, len(flag_cols) * 0.6 + 1))
    fig, ax = plt.subplots(figsize=(10, fig_h))
    for idx, col in enumerate(flag_cols):
        ax.step(df[x_col], pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int) + idx * 1.5, where="post")
    ax.set_yticks([idx * 1.5 + 0.5 for idx in range(len(flag_cols))]); ax.set_yticklabels(flag_cols)
    ax.set_xlabel(x_label); ax.set_ylabel("Flag")
    ax.set_title(f"{title_prefix + ' - ' if title_prefix else ''}Test Flags Timeline")
    ax.grid(True, axis="x", alpha=0.3); fig.tight_layout(); fig.savefig(out_dir / "test_flags_timeline.png", dpi=150); plt.close(fig)
    return True


def plot_supervisor_status(df, x_col, x_label, status_col, out_dir, args):
    if status_col is None:
        print("Warning: cannot generate supervisor_status_timeline.png; missing status column.")
        return False, False
    s = df[status_col].fillna("unknown").astype(str).str.lower()
    preferred = ["unknown", "good", "degraded", "recovering", "invalid"]
    present = list(dict.fromkeys(s.tolist()))
    ordered = [x for x in preferred if x in present] + [x for x in present if x not in preferred]
    mapping = {label: i for i, label in enumerate(ordered)}
    vals = s.map(mapping)
    transitions = df.index[s.ne(s.shift(1))].tolist()[1:]
    fig, ax = plt.subplots(figsize=(10, 4)); ax.step(df[x_col], vals, where="post")
    for idx in transitions[: args.max_event_markers]:
        ax.axvline(df.at[idx, x_col], color="gray", alpha=0.2, linewidth=0.8)
    ax.set_yticks(list(mapping.values())); ax.set_yticklabels(list(mapping.keys()))
    ax.set_xlabel(x_label); ax.set_ylabel("Status")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Supervisor Status Timeline")
    ax.grid(True, axis="x", alpha=0.3); fig.tight_layout(); fig.savefig(out_dir / "supervisor_status_timeline.png", dpi=150); plt.close(fig)

    invalid_mask = s.eq("invalid")
    invalid_edge = invalid_mask.ne(invalid_mask.shift(1, fill_value=False)) & (invalid_mask | invalid_mask.shift(1, fill_value=False))
    idxs = df.index[invalid_mask | invalid_edge]
    if idxs.empty:
        print("Warning: skipping invalid_events_zoom.png; no invalid events found.")
        return True, False
    win = args.state_zoom_window_min if args.time_units == "min" else args.state_zoom_window_min * 60.0
    xmin = df.loc[idxs, x_col].min() - win; xmax = df.loc[idxs, x_col].max() + win
    zoom = df[(df[x_col] >= xmin) & (df[x_col] <= xmax)]
    fig, ax = plt.subplots(figsize=(10, 4)); ax.step(zoom[x_col], zoom[status_col].fillna("unknown").astype(str).str.lower().map(mapping), where="post")
    ax.set_yticks(list(mapping.values())); ax.set_yticklabels(list(mapping.keys()))
    ax.set_xlabel(x_label); ax.set_ylabel("Status")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Invalid Event Context (Zoom)")
    ax.grid(True, axis="x", alpha=0.3); fig.tight_layout(); fig.savefig(out_dir / "invalid_events_zoom.png", dpi=150); plt.close(fig)
    return True, True


def plot_fused_score(df, x_col, x_label, out_dir, args):
    col = find_column(df, FUSED_SCORE_ALIASES)
    if col is None:
        print("Warning: skipping fused_score.png; no fused score column.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4)); ax.plot(df[x_col], pd.to_numeric(df[col], errors="coerce"), label=col)
    ax.axhline(0.8, linestyle="--", color="green", alpha=0.6); ax.axhline(0.5, linestyle="--", color="red", alpha=0.6)
    ax.set_xlabel(x_label); ax.set_ylabel("Fused score")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Fused Score")
    ax.grid(True, alpha=0.3); fig.tight_layout(); fig.savefig(out_dir / "fused_score.png", dpi=150); plt.close(fig)
    return True


def plot_hdop_sats(df, x_col, x_label, out_dir, args):
    hdop_col = find_column(df, HDOP_ALIASES); sats_col = find_column(df, NUM_SATS_ALIASES)
    if hdop_col is None and sats_col is None:
        print("Warning: skipping hdop_sats.png; no HDOP/satellite columns.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4)); ax2 = None
    if hdop_col is not None:
        ax.plot(df[x_col], pd.to_numeric(df[hdop_col], errors="coerce"), color="tab:purple", label="HDOP")
        ax.set_ylabel("HDOP", color="tab:purple"); ax.tick_params(axis="y", labelcolor="tab:purple")
    if sats_col is not None:
        if hdop_col is not None:
            ax2 = ax.twinx(); ax2.plot(df[x_col], pd.to_numeric(df[sats_col], errors="coerce"), color="tab:green", label="Satellites")
            ax2.set_ylabel("Satellites", color="tab:green"); ax2.tick_params(axis="y", labelcolor="tab:green")
        else:
            ax.plot(df[x_col], pd.to_numeric(df[sats_col], errors="coerce"), color="tab:green", label="Satellites")
            ax.set_ylabel("Satellites")
    ax.set_xlabel(x_label); ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}GNSS Quality (HDOP / Satellites)")
    ax.grid(True, alpha=0.3); fig.tight_layout(); fig.savefig(out_dir / "hdop_sats.png", dpi=150); plt.close(fig)
    return True


def plot_fix_valid(df, x_col, x_label, out_dir, args):
    col = find_column(df, FIX_VALID_ALIASES)
    if col is None:
        print("Warning: skipping fix_valid_timeline.png; no fix valid column.")
        return False
    vals = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0, upper=1)
    fig, ax = plt.subplots(figsize=(10, 3)); ax.step(df[x_col], vals, where="post")
    ax.set_yticks([0, 1]); ax.set_yticklabels(["invalid", "valid"])
    ax.set_xlabel(x_label); ax.set_ylabel("GNSS fix")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Fix Valid Timeline")
    ax.grid(True, axis="x", alpha=0.3); fig.tight_layout(); fig.savefig(out_dir / "fix_valid_timeline.png", dpi=150); plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate meeting/reporting figures from supervisor CSV outputs.")
    parser.add_argument("--csv", required=True); parser.add_argument("--out-dir", required=True)
    parser.add_argument("--speed-threshold-mps", type=float, default=40.0)
    parser.add_argument("--accel-threshold-mps2", type=float, default=15.0)
    parser.add_argument("--min-movement-m", type=float, default=0.5)
    parser.add_argument("--time-units", choices=["s", "min"], default="min")
    parser.add_argument("--clip-movement-m", type=float, default=500.0)
    parser.add_argument("--include-raw-movement", action="store_true")
    parser.add_argument("--state-zoom-window-min", type=float, default=2.0)
    parser.add_argument("--max-event-markers", type=int, default=200)
    parser.add_argument("--title-prefix", default="")
    args = parser.parse_args()

    df = pd.read_csv(args.csv); out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    t_col = find_column(df, TIME_ALIASES)
    if t_col is None:
        print(f"Warning: no time column found from aliases {TIME_ALIASES}; using row index as x-axis.")
        df = df.copy(); t_col = "__row_idx__"; df[t_col] = range(len(df))
    x_col, x_label = add_relative_time_column(df, t_col, args.time_units)

    created, skipped = [], []
    def track(name, ok): (created if ok else skipped).append(name)

    track("position_error.png", plot_position_error(df, x_col, x_label, out_dir, args.title_prefix))
    track("speed_accel_thresholds.png", plot_speed_accel(df, x_col, x_label, find_column(df, SPEED_ALIASES), find_column(df, ACCEL_ALIASES), out_dir, args))
    track("movement_gate.png", plot_movement_gate(df, x_col, x_label, find_column(df, MOVEMENT_ALIASES), out_dir, args))
    track("test_flags_timeline.png", plot_test_flags(df, x_col, x_label, find_test_flag_columns(df), out_dir, args.title_prefix))
    status_ok, invalid_ok = plot_supervisor_status(df, x_col, x_label, find_column(df, STATUS_ALIASES), out_dir, args)
    track("supervisor_status_timeline.png", status_ok); track("invalid_events_zoom.png", invalid_ok)
    track("fused_score.png", plot_fused_score(df, x_col, x_label, out_dir, args))
    track("hdop_sats.png", plot_hdop_sats(df, x_col, x_label, out_dir, args))
    track("fix_valid_timeline.png", plot_fix_valid(df, x_col, x_label, out_dir, args))

    print(f"Generated {len(created)} figures in {out_dir}")
    print(f"Created: {', '.join(created) if created else 'none'}")
    print(f"Skipped: {', '.join(skipped) if skipped else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
