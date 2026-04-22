#!/usr/bin/env python3
"""CLI helper to run a replay and write output artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pnt_supervisor.adapters import ArduPilotLogXLSXAdapter, NMEAReplayAdapter
from pnt_supervisor.core.config import AppConfig
from pnt_supervisor.evaluation import ReplayRunner


DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "default_multirotor.json"


def _build_adapter(input_path: Path, source_type: str):
    if source_type == "xlsx":
        return ArduPilotLogXLSXAdapter(input_path)
    if source_type == "nmea":
        return NMEAReplayAdapter(input_path)
    raise ValueError(f"Unsupported source type: {source_type}")


def _load_config(path: Path) -> AppConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AppConfig(**payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input replay file (.xlsx, .txt/.log/.nmea)")
    parser.add_argument("--source-type", required=True, choices=["xlsx", "nmea"], help="Input source type")
    parser.add_argument("--out-dir", required=True, type=Path, help="Directory where output reports are written")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="App config JSON to use (default: configs/default_multirotor.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = _load_config(args.config)
    adapter = _build_adapter(args.input, args.source_type)

    runner = ReplayRunner(adapter, config=config)
    result = runner.run(args.out_dir)

    print("Replay completed.")
    print(f"  input: {args.input}")
    print(f"  source_type: {args.source_type}")
    print(f"  out_dir: {args.out_dir}")
    print(f"  epochs: {result.summary['total_epochs']}")
    print(f"  invalid_events: {result.summary['invalid_events']}")
    print(f"  degraded_events: {result.summary['degraded_events']}")
    print("  outputs:")
    for key, path in result.output_paths.items():
        print(f"    - {key}: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
