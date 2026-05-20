"""CLI entry point for running offline replay from supported input formats."""

from __future__ import annotations

import argparse
from pathlib import Path

from pnt_supervisor.adapters import ArduPilotExcelObservationAdapter
from pnt_supervisor.evaluation import ReplayRunner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input replay file path")
    parser.add_argument(
        "--input-format",
        default="ardupilot_excel",
        choices=["ardupilot_excel"],
        help="Input adapter format",
    )
    parser.add_argument("--sheet", default="in", help="Excel sheet name")
    parser.add_argument("--out-dir", required=True, type=Path, help="Directory where replay artifacts are written")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.input_format == "ardupilot_excel":
        adapter = ArduPilotExcelObservationAdapter(args.input, sheet_name=args.sheet)
    else:
        raise ValueError(f"Unsupported input format: {args.input_format}")

    result = ReplayRunner(adapter).run(args.out_dir)

    print(f"Output directory: {args.out_dir}")
    print("Generated files:")
    for path in result.output_paths.values():
        print(f"- {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
