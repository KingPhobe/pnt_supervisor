#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
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
REASONS_ALIASES = ["reasons", "reason", "reason_codes"]
EMPTY_REASON_VALUES = {"", "nan", "none", "null", "na", "n/a", "[]"}


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
    df["__time_s__"] = numeric_t
    return "__time_rel__", f"Time since start ({units})"


def make_gap_broken_series(
    time_rel,
    values,
    original_time_s=None,
    gap_break_s: float = 10.0,
    time_units: str = "min",
) -> tuple[list[float], list[float]]:
    """Insert NaNs before samples that follow large time gaps to avoid false line joins."""
    x_vals = pd.to_numeric(pd.Series(time_rel), errors="coerce").tolist()
    y_vals = pd.to_numeric(pd.Series(values), errors="coerce").tolist()
    if original_time_s is not None:
        dt_basis = pd.to_numeric(pd.Series(original_time_s), errors="coerce").tolist()
        scale = 1.0
    else:
        dt_basis = x_vals
        scale = 60.0 if time_units == "min" else 1.0

    x_plot: list[float] = []
    y_plot: list[float] = []
    prev_t = None
    for x, y, t in zip(x_vals, y_vals, dt_basis, strict=False):
        if prev_t is not None and pd.notna(t) and pd.notna(prev_t):
            if (float(t) - float(prev_t)) * scale > gap_break_s:
                x_plot.append(float("nan"))
                y_plot.append(float("nan"))
        x_plot.append(x)
        y_plot.append(y)
        if pd.notna(t):
            prev_t = t
    return x_plot, y_plot


def _gap_plot_args(df: pd.DataFrame, x_col: str, values, args) -> tuple[list[float], list[float]]:
    original_time_s = df["__time_s__"] if "__time_s__" in df.columns else None
    return make_gap_broken_series(df[x_col], values, original_time_s, args.gap_break_s, args.time_units)


def find_test_flag_columns(df: pd.DataFrame) -> list[str]:
    exclude = set(
        TIME_ALIASES
        + POSITION_ERROR_ALIASES
        + SPEED_ALIASES
        + ACCEL_ALIASES
        + MOVEMENT_ALIASES
        + FUSED_SCORE_ALIASES
        + HDOP_ALIASES
        + NUM_SATS_ALIASES
        + STATUS_ALIASES
        + REASONS_ALIASES
    )
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
    fig.tight_layout()
    fig.savefig(out_dir / "position_error.png", dpi=150)
    plt.close(fig)
    return True


def plot_speed_accel(df, x_col, x_label, speed_col, accel_col, out_dir, args):
    if speed_col is None and accel_col is None:
        print("Warning: cannot generate speed_accel_thresholds.png; missing speed and acceleration columns.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4))
    ax2 = None
    if speed_col is not None:
        speed = pd.to_numeric(df[speed_col], errors="coerce")
        x_speed, y_speed = _gap_plot_args(df, x_col, speed, args)
        ax.plot(x_speed, y_speed, color="tab:blue", label="GPS speed")
        ax.axhline(args.speed_threshold_mps, linestyle="--", color="tab:blue", alpha=0.7, label=f"speed threshold ({args.speed_threshold_mps} m/s)")
        ax.set_ylabel("GPS speed (m/s)", color="tab:blue")
        ax.tick_params(axis="y", labelcolor="tab:blue")
    if accel_col is not None:
        accel = pd.to_numeric(df[accel_col], errors="coerce")
        x_accel, y_accel = _gap_plot_args(df, x_col, accel, args)
        if speed_col is not None:
            ax2 = ax.twinx()
            ax2.plot(x_accel, y_accel, color="tab:orange", label="GPS acceleration")
            ax2.axhline(args.accel_threshold_mps2, linestyle=":", color="tab:orange", alpha=0.7, label=f"accel threshold ({args.accel_threshold_mps2} m/s²)")
            ax2.set_ylabel("GPS acceleration (m/s²)", color="tab:orange")
            ax2.tick_params(axis="y", labelcolor="tab:orange")
        else:
            ax.plot(x_accel, y_accel, color="tab:orange", label="GPS acceleration")
            ax.axhline(args.accel_threshold_mps2, linestyle=":", color="tab:orange", alpha=0.7, label=f"accel threshold ({args.accel_threshold_mps2} m/s²)")
            ax.set_ylabel("GPS acceleration (m/s²)")
    ax.set_xlabel(x_label)
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Speed and Acceleration Thresholds")
    ax.grid(True, alpha=0.3)
    lines, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        l2, lb2 = ax2.get_legend_handles_labels()
        lines += l2
        labels += lb2
    ax.legend(lines, labels, loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "speed_accel_thresholds.png", dpi=150)
    plt.close(fig)
    return True


def plot_movement_gate(df, x_col, x_label, movement_col, out_dir, args):
    if movement_col is None:
        print("Warning: cannot generate movement_gate.png; missing movement column.")
        return False
    movement = pd.to_numeric(df[movement_col], errors="coerce")
    clip_active = movement_col.lower() == "jump_distance_m" or movement.max(skipna=True) > args.clip_movement_m
    display = movement.clip(upper=args.clip_movement_m) if clip_active else movement
    x_move, y_move = _gap_plot_args(df, x_col, display, args)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x_move, y_move, label=movement_col)
    ax.axhline(args.min_movement_m, linestyle="--", label=f"min movement ({args.min_movement_m} m)")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Movement / jump distance (m)")
    suffix = f" (clipped at {args.clip_movement_m:g} m)" if clip_active else ""
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Movement Gate{suffix}")
    if clip_active:
        ax.text(0.01, 0.98, "Large GNSS jumps are clipped for readability", transform=ax.transAxes, va="top", fontsize=9)
        if args.include_raw_movement:
            raw_x, raw_y = _gap_plot_args(df, x_col, movement, args)
            ax.plot(raw_x, raw_y, alpha=0.18, linewidth=0.8, label=f"{movement_col} raw")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "movement_gate.png", dpi=150)
    plt.close(fig)
    return True


def plot_test_flags(df, x_col, x_label, flag_cols, out_dir, title_prefix):
    if not flag_cols:
        print("Warning: cannot generate test_flags_timeline.png; no matching test flag columns found.")
        return False
    plotted_cols = []
    constant_zero_cols = []
    for col in flag_cols:
        vals = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0, upper=1)
        if col.lower() in {"warning_flag", "fault_flag"} and vals.max() == 0 and vals.min() == 0:
            constant_zero_cols.append(col)
        else:
            plotted_cols.append((col, vals))
    if not plotted_cols and constant_zero_cols:
        plotted_cols = [(col, pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0, upper=1)) for col in constant_zero_cols[:1]]
    fig_h = max(3, min(20, len(plotted_cols) * 0.6 + 1))
    fig, ax = plt.subplots(figsize=(10, fig_h))
    for idx, (col, vals) in enumerate(plotted_cols):
        ax.step(df[x_col], vals + idx * 1.5, where="post", label=col)
    ax.set_yticks([idx * 1.5 + 0.5 for idx in range(len(plotted_cols))])
    ax.set_yticklabels([col for col, _ in plotted_cols])
    ax.set_xlabel(x_label)
    ax.set_ylabel("Flag")
    suffix = f" ({', '.join(constant_zero_cols)} constant zero)" if constant_zero_cols else ""
    ax.set_title(f"{title_prefix + ' - ' if title_prefix else ''}Test Flags Timeline{suffix}")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "test_flags_timeline.png", dpi=150)
    plt.close(fig)
    return True


def _status_mapping(status: pd.Series) -> dict[str, int]:
    preferred = ["unknown", "good", "degraded", "recovering", "invalid"]
    present = list(dict.fromkeys(status.tolist()))
    ordered = [x for x in preferred if x in present] + [x for x in present if x not in preferred]
    return {label: i for i, label in enumerate(ordered)}


def _plot_status_base(ax, rows: pd.DataFrame, x_col: str, status_col: str, mapping: dict[str, int]):
    status = rows[status_col].fillna("unknown").astype(str).str.lower()
    ax.step(rows[x_col], status.map(mapping), where="post", color="tab:blue", label="supervisor state")
    ax.set_yticks(list(mapping.values()))
    ax.set_yticklabels(list(mapping.keys()))
    ax.set_ylabel("Status")


def _invalid_clusters(df: pd.DataFrame, x_col: str, invalid_mask: pd.Series, window: float) -> list[tuple[float, float, list[int]]]:
    invalid_rows = df.loc[invalid_mask & pd.notna(df[x_col]), [x_col]]
    clusters: list[tuple[float, float, list[int]]] = []
    current_start = None
    current_end = None
    current_idxs: list[int] = []
    for idx, row in invalid_rows.iterrows():
        t = float(row[x_col])
        if current_start is None or (current_end is not None and t - current_end >= window):
            if current_start is not None and current_end is not None:
                clusters.append((current_start, current_end, current_idxs))
            current_start = t
            current_idxs = [idx]
        else:
            current_idxs.append(idx)
        current_end = t
    if current_start is not None and current_end is not None:
        clusters.append((current_start, current_end, current_idxs))
    return clusters


def plot_supervisor_status(df, x_col, x_label, status_col, out_dir, args):
    if status_col is None:
        print("Warning: cannot generate supervisor_status_timeline.png; missing status column.")
        return False, []
    s = df[status_col].fillna("unknown").astype(str).str.lower()
    mapping = _status_mapping(s)
    vals = s.map(mapping)
    transitions = df.index[s.ne(s.shift(1))].tolist()[1:]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.step(df[x_col], vals, where="post", color="tab:blue")
    for idx in transitions[: args.max_event_markers]:
        ax.axvline(df.at[idx, x_col], color="gray", alpha=0.2, linewidth=0.8)
    ax.set_yticks(list(mapping.values()))
    ax.set_yticklabels(list(mapping.keys()))
    ax.set_xlabel(x_label)
    ax.set_ylabel("Status")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Supervisor Status Timeline")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "supervisor_status_timeline.png", dpi=150)
    plt.close(fig)

    invalid_mask = s.eq("invalid")
    if not invalid_mask.any():
        print("Warning: skipping invalid event plots; no invalid events found.")
        return True, []

    invalid_times = df.loc[invalid_mask, x_col]
    fig, ax = plt.subplots(figsize=(10, 4))
    _plot_status_base(ax, df, x_col, status_col, mapping)
    for t in invalid_times.iloc[: args.max_event_markers]:
        ax.axvline(t, color="red", alpha=0.15, linewidth=0.8)
    ax.set_xlabel(x_label)
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Invalid Events Overview")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "invalid_events_overview.png", dpi=150)
    plt.close(fig)

    win = args.state_zoom_window_min if args.time_units == "min" else args.state_zoom_window_min * 60.0
    clusters = _invalid_clusters(df, x_col, invalid_mask, win)
    data_min = float(pd.to_numeric(df[x_col], errors="coerce").min())
    data_max = float(pd.to_numeric(df[x_col], errors="coerce").max())
    created = ["invalid_events_overview.png"]
    score_col = find_column(df, FUSED_SCORE_ALIASES)
    fix_col = find_column(df, FIX_VALID_ALIASES)
    for plot_idx, (cluster_start, cluster_end, _) in enumerate(clusters[: args.max_invalid_zoom_plots], start=1):
        xmin = max(data_min, cluster_start - win)
        xmax = min(data_max, cluster_end + win)
        zoom = df[(df[x_col] >= xmin) & (df[x_col] <= xmax)]
        if zoom.empty:
            continue
        fig, ax = plt.subplots(figsize=(10, 4))
        _plot_status_base(ax, zoom, x_col, status_col, mapping)
        center = (cluster_start + cluster_end) / 2.0
        ax.axvline(center, color="red", linestyle="--", alpha=0.8, linewidth=1.1, label="invalid cluster center")
        if score_col is not None:
            ax2 = ax.twinx()
            score = pd.to_numeric(zoom[score_col], errors="coerce")
            ax2.plot(zoom[x_col], score, color="tab:orange", alpha=0.6, linewidth=1.2, label="fused_score")
            ax2.set_ylabel("Fused score / fix_valid")
            ax2.set_ylim(-0.05, 1.05)
            if fix_col is not None:
                fix = pd.to_numeric(zoom[fix_col], errors="coerce").fillna(0).clip(lower=0, upper=1)
                ax2.step(zoom[x_col], fix, where="post", color="tab:green", alpha=0.35, linewidth=1.0, label="fix_valid")
        elif fix_col is not None:
            ax2 = ax.twinx()
            fix = pd.to_numeric(zoom[fix_col], errors="coerce").fillna(0).clip(lower=0, upper=1)
            ax2.step(zoom[x_col], fix, where="post", color="tab:green", alpha=0.35, linewidth=1.0, label="fix_valid")
            ax2.set_ylabel("fix_valid")
            ax2.set_ylim(-0.05, 1.05)
        ax.set_xlim(xmin, xmax)
        ax.set_xlabel(x_label)
        ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Invalid Event Zoom {plot_idx:03d} ({xmin:.1f}–{xmax:.1f} {args.time_units})")
        ax.grid(True, axis="x", alpha=0.3)
        fig.tight_layout()
        filename = f"invalid_event_zoom_{plot_idx:03d}.png"
        fig.savefig(out_dir / filename, dpi=150)
        plt.close(fig)
        created.append(filename)
    return True, created


def plot_fused_score(df, x_col, x_label, out_dir, args):
    col = find_column(df, FUSED_SCORE_ALIASES)
    if col is None:
        print("Warning: skipping fused_score.png; no fused score column.")
        return False
    score = pd.to_numeric(df[col], errors="coerce")
    x_score, y_score = _gap_plot_args(df, x_col, score, args)
    marker = "o" if score.notna().sum() <= 40 else None
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x_score, y_score, marker=marker, markersize=3 if marker else None, linewidth=1.5, label=col)
    ax.axhline(0.8, linestyle="--", color="green", alpha=0.6, label="nominal guide (0.8)")
    ax.axhline(0.5, linestyle="--", color="red", alpha=0.6, label="invalid guide (0.5)")
    status_col = find_column(df, STATUS_ALIASES)
    if status_col is not None:
        status = df[status_col].fillna("unknown").astype(str).str.lower()
        transitions = df.index[status.ne(status.shift(1))].tolist()[1 : args.max_event_markers + 1]
        for idx in transitions:
            ax.axvline(df.at[idx, x_col], color="gray", alpha=0.12, linewidth=0.8)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Fused score")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Fused Score")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "fused_score.png", dpi=150)
    plt.close(fig)
    return True


def plot_hdop_sats(df, x_col, x_label, out_dir, args):
    hdop_col = find_column(df, HDOP_ALIASES)
    sats_col = find_column(df, NUM_SATS_ALIASES)
    if hdop_col is None and sats_col is None:
        print("Warning: skipping hdop_sats.png; no HDOP/satellite columns.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4))
    ax2 = None
    clipped = False
    if hdop_col is not None:
        hdop = pd.to_numeric(df[hdop_col], errors="coerce")
        clipped = args.clip_hdop is not None and hdop.max(skipna=True) > args.clip_hdop
        display_hdop = hdop.clip(upper=args.clip_hdop) if clipped else hdop
        x_hdop, y_hdop = _gap_plot_args(df, x_col, display_hdop, args)
        ax.plot(x_hdop, y_hdop, color="tab:purple", label="HDOP")
        ax.set_ylabel("HDOP", color="tab:purple")
        ax.tick_params(axis="y", labelcolor="tab:purple")
        if clipped:
            ax.text(0.01, 0.98, "HDOP clipped for readability", transform=ax.transAxes, va="top", fontsize=9)
    if sats_col is not None:
        sats = pd.to_numeric(df[sats_col], errors="coerce")
        x_sats, y_sats = _gap_plot_args(df, x_col, sats, args)
        if hdop_col is not None:
            ax2 = ax.twinx()
            ax2.plot(x_sats, y_sats, color="tab:green", label="Satellites")
            ax2.set_ylabel("Satellites", color="tab:green")
            ax2.tick_params(axis="y", labelcolor="tab:green")
        else:
            ax.plot(x_sats, y_sats, color="tab:green", label="Satellites")
            ax.set_ylabel("Satellites")
    suffix = f" (HDOP clipped at {args.clip_hdop:g})" if clipped else ""
    ax.set_xlabel(x_label)
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}GNSS Quality (HDOP / Satellites){suffix}")
    ax.grid(True, alpha=0.3)
    lines, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        l2, lb2 = ax2.get_legend_handles_labels()
        lines += l2
        labels += lb2
    if lines:
        ax.legend(lines, labels, loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "hdop_sats.png", dpi=150)
    plt.close(fig)
    return True


def plot_fix_valid(df, x_col, x_label, out_dir, args):
    col = find_column(df, FIX_VALID_ALIASES)
    if col is None:
        print("Warning: skipping fix_valid_timeline.png; no fix valid column.")
        return False
    vals = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0, upper=1)
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.step(df[x_col], vals, where="post")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["invalid", "valid"])
    ax.set_xlabel(x_label)
    ax.set_ylabel("GNSS fix")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Fix Valid Timeline")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "fix_valid_timeline.png", dpi=150)
    plt.close(fig)
    return True


def _split_reason_codes(value) -> list[str]:
    if pd.isna(value):
        return []
    parts = []
    for raw in str(value).split("|"):
        code = raw.strip()
        if code.lower() not in EMPTY_REASON_VALUES:
            parts.append(code)
    return parts


def plot_reason_codes_timeline(df, x_col, x_label, out_dir, args):
    col = find_column(df, REASONS_ALIASES)
    if col is None:
        print("Warning: skipping reason_codes_timeline.png; no reasons column.")
        return False
    row_codes = df[col].apply(_split_reason_codes)
    counts = Counter(code for codes in row_codes for code in codes)
    if not counts:
        print("Warning: skipping reason_codes_timeline.png; no non-empty reason codes.")
        return False
    top_codes = [code for code, _ in counts.most_common(args.reason_max_codes)]
    y_lookup = {code: idx for idx, code in enumerate(top_codes)}
    xs: list[float] = []
    ys: list[int] = []
    for t, codes in zip(df[x_col], row_codes, strict=False):
        active = {code for code in codes if code in y_lookup}
        for code in active:
            xs.append(t)
            ys.append(y_lookup[code])
    fig_h = max(3, min(12, len(top_codes) * 0.55 + 1.2))
    fig, ax = plt.subplots(figsize=(10, fig_h))
    ax.scatter(xs, ys, marker="|", s=130, linewidths=1.8, color="tab:red")
    ax.set_yticks(list(y_lookup.values()))
    ax.set_yticklabels(top_codes)
    ax.set_ylim(-0.75, len(top_codes) - 0.25)
    ax.set_xlabel(x_label)
    ax.set_ylabel("Reason code")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Reason Codes Timeline (top {len(top_codes)})")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "reason_codes_timeline.png", dpi=150)
    plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate meeting/reporting figures from supervisor CSV outputs.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--speed-threshold-mps", type=float, default=40.0)
    parser.add_argument("--accel-threshold-mps2", type=float, default=15.0)
    parser.add_argument("--min-movement-m", type=float, default=0.5)
    parser.add_argument("--time-units", choices=["s", "min"], default="min")
    parser.add_argument("--clip-movement-m", type=float, default=500.0)
    parser.add_argument("--include-raw-movement", action="store_true")
    parser.add_argument("--state-zoom-window-min", type=float, default=2.0)
    parser.add_argument("--max-event-markers", type=int, default=200)
    parser.add_argument("--gap-break-s", type=float, default=10.0)
    parser.add_argument("--clip-hdop", type=float, default=20.0)
    parser.add_argument("--max-invalid-zoom-plots", type=int, default=6)
    parser.add_argument("--reason-max-codes", type=int, default=12)
    parser.add_argument("--title-prefix", default="")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t_col = find_column(df, TIME_ALIASES)
    if t_col is None:
        print(f"Warning: no time column found from aliases {TIME_ALIASES}; using row index as x-axis.")
        df = df.copy()
        t_col = "__row_idx__"
        df[t_col] = range(len(df))
    x_col, x_label = add_relative_time_column(df, t_col, args.time_units)

    created: list[str] = []
    skipped: list[str] = []

    def track(name: str, ok: bool, reason: str = "not generated"):
        if ok:
            created.append(name)
        else:
            skipped.append(f"{name} ({reason})")

    track("position_error.png", plot_position_error(df, x_col, x_label, out_dir, args.title_prefix), "missing position error column")
    track(
        "speed_accel_thresholds.png",
        plot_speed_accel(df, x_col, x_label, find_column(df, SPEED_ALIASES), find_column(df, ACCEL_ALIASES), out_dir, args),
        "missing speed and acceleration columns",
    )
    track("movement_gate.png", plot_movement_gate(df, x_col, x_label, find_column(df, MOVEMENT_ALIASES), out_dir, args), "missing movement column")
    track("test_flags_timeline.png", plot_test_flags(df, x_col, x_label, find_test_flag_columns(df), out_dir, args.title_prefix), "no matching test flag columns")
    status_ok, invalid_created = plot_supervisor_status(df, x_col, x_label, find_column(df, STATUS_ALIASES), out_dir, args)
    track("supervisor_status_timeline.png", status_ok, "missing status column")
    if invalid_created:
        created.extend(invalid_created)
    else:
        skipped.append("invalid_events_overview.png / invalid_event_zoom_*.png (no invalid events or missing status column)")
    track("fused_score.png", plot_fused_score(df, x_col, x_label, out_dir, args), "missing fused score column")
    track("hdop_sats.png", plot_hdop_sats(df, x_col, x_label, out_dir, args), "missing HDOP/satellite columns")
    track("fix_valid_timeline.png", plot_fix_valid(df, x_col, x_label, out_dir, args), "missing fix valid column")
    track("reason_codes_timeline.png", plot_reason_codes_timeline(df, x_col, x_label, out_dir, args), "missing or empty reasons column")

    print(f"Generated {len(created)} figures in {out_dir}")
    print("Created figures:")
    for name in created:
        print(f"  - {name}")
    print("Skipped plots:")
    if skipped:
        for item in skipped:
            print(f"  - {item}")
    else:
        print("  - none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
