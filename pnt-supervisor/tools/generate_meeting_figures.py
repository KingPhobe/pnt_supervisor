#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

TIME_ALIASES = ["t", "time", "time_s", "timestamp", "epoch_s"]
POSITION_ERROR_ALIASES = ["position_error", "position_error_m", "pos_error", "pos_error_m", "horizontal_error_m"]
SPEED_ALIASES = ["speed", "speed_mps", "ground_speed", "ground_speed_mps"]
ACCEL_ALIASES = ["acceleration", "accel", "accel_mps2", "acceleration_mps2"]
MOVEMENT_ALIASES = ["movement", "movement_m", "displacement", "displacement_m", "window_displacement_m"]
STATUS_ALIASES = ["supervisor_status", "status", "pnt_status", "nav_status"]


def find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lower_to_actual = {col.lower(): col for col in df.columns}
    for alias in aliases:
        if alias.lower() in lower_to_actual:
            return lower_to_actual[alias.lower()]
    return None


def find_test_flag_columns(df: pd.DataFrame) -> list[str]:
    flag_cols: list[str] = []
    for col in df.columns:
        norm = col.lower()
        if not (norm.startswith("test_") or norm.endswith("_pass") or norm.endswith("_valid") or norm.endswith("_ok")):
            continue
        series = df[col]
        if pd.api.types.is_bool_dtype(series) or pd.api.types.is_integer_dtype(series):
            flag_cols.append(col)
    return flag_cols


def plot_position_error(df: pd.DataFrame, t_col: str, out_dir: Path, title_prefix: str) -> bool:
    position_col = find_column(df, POSITION_ERROR_ALIASES)
    if position_col is None:
        print("Warning: cannot generate position_error.png; missing position error column.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df[t_col], df[position_col])
    ax.set_xlabel(t_col)
    ax.set_ylabel("Position Error (m)")
    ax.set_title(f"{title_prefix + ' - ' if title_prefix else ''}Position Error vs Time")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "position_error.png", dpi=150)
    plt.close(fig)
    return True


def plot_speed_accel(df: pd.DataFrame, t_col: str, speed_col: str | None, accel_col: str | None, out_dir: Path, args: argparse.Namespace) -> bool:
    if speed_col is None and accel_col is None:
        print("Warning: cannot generate speed_accel_thresholds.png; missing speed and acceleration columns.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4))
    if speed_col is not None:
        ax.plot(df[t_col], df[speed_col], label=speed_col)
        ax.axhline(args.speed_threshold_mps, linestyle="--", label=f"speed threshold ({args.speed_threshold_mps} m/s)")
    else:
        print("Warning: speed column missing; plotting acceleration only.")
    if accel_col is not None:
        ax.plot(df[t_col], df[accel_col], label=accel_col)
        ax.axhline(args.accel_threshold_mps2, linestyle=":", label=f"accel threshold ({args.accel_threshold_mps2} m/s²)")
    else:
        print("Warning: acceleration column missing; plotting speed only.")
    ax.set_xlabel(t_col)
    ax.set_ylabel("Value")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Speed and Acceleration Thresholds")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "speed_accel_thresholds.png", dpi=150)
    plt.close(fig)
    return True


def plot_movement_gate(df: pd.DataFrame, t_col: str, movement_col: str | None, out_dir: Path, args: argparse.Namespace) -> bool:
    if movement_col is None:
        print("Warning: cannot generate movement_gate.png; missing movement column.")
        return False
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df[t_col], df[movement_col], label=movement_col)
    ax.axhline(args.min_movement_m, linestyle="--", label=f"min movement ({args.min_movement_m} m)")
    ax.set_xlabel(t_col)
    ax.set_ylabel("Movement (m)")
    ax.set_title(f"{args.title_prefix + ' - ' if args.title_prefix else ''}Movement Gate")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "movement_gate.png", dpi=150)
    plt.close(fig)
    return True


def plot_test_flags(df: pd.DataFrame, t_col: str, flag_cols: list[str], out_dir: Path, title_prefix: str) -> bool:
    if not flag_cols:
        print("Warning: cannot generate test_flags_timeline.png; no matching test flag columns found.")
        return False
    fig, ax = plt.subplots(figsize=(10, max(3, len(flag_cols) * 0.6)))
    for idx, col in enumerate(flag_cols):
        ax.step(df[t_col], df[col].astype(int) + idx * 1.5, where="post")
    ax.set_yticks([idx * 1.5 + 0.5 for idx in range(len(flag_cols))])
    ax.set_yticklabels(flag_cols)
    ax.set_xlabel(t_col)
    ax.set_ylabel("Flag")
    ax.set_title(f"{title_prefix + ' - ' if title_prefix else ''}Test Flags Timeline")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "test_flags_timeline.png", dpi=150)
    plt.close(fig)
    return True


def plot_supervisor_status(df: pd.DataFrame, t_col: str, status_col: str | None, out_dir: Path, title_prefix: str) -> bool:
    if status_col is None:
        print("Warning: cannot generate supervisor_status_timeline.png; missing status column.")
        return False
    status = df[status_col].astype(str)
    labels = list(dict.fromkeys(status))
    mapping = {label: i for i, label in enumerate(labels)}
    status_values = status.map(mapping)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.step(df[t_col], status_values, where="post")
    ax.set_yticks(list(mapping.values()))
    ax.set_yticklabels(list(mapping.keys()))
    ax.set_xlabel(t_col)
    ax.set_ylabel("Status")
    ax.set_title(f"{title_prefix + ' - ' if title_prefix else ''}Supervisor Status Timeline")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "supervisor_status_timeline.png", dpi=150)
    plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate meeting/reporting figures from supervisor CSV outputs.")
    parser.add_argument("--csv", required=True, help="Path to test/simulation results CSV file.")
    parser.add_argument("--out-dir", required=True, help="Directory to write PNG outputs.")
    parser.add_argument("--speed-threshold-mps", type=float, default=40.0)
    parser.add_argument("--accel-threshold-mps2", type=float, default=15.0)
    parser.add_argument("--min-movement-m", type=float, default=0.5)
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

    speed_col = find_column(df, SPEED_ALIASES)
    accel_col = find_column(df, ACCEL_ALIASES)
    movement_col = find_column(df, MOVEMENT_ALIASES)
    status_col = find_column(df, STATUS_ALIASES)
    flag_cols = find_test_flag_columns(df)

    plot_position_error(df, t_col, out_dir, args.title_prefix)
    plot_speed_accel(df, t_col, speed_col, accel_col, out_dir, args)
    plot_movement_gate(df, t_col, movement_col, out_dir, args)
    plot_test_flags(df, t_col, flag_cols, out_dir, args.title_prefix)
    plot_supervisor_status(df, t_col, status_col, out_dir, args.title_prefix)

    print(f"Done. Figures written to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
