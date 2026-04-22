"""CSV export helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CsvWriter:
    """Write rows of dictionaries to CSV."""

    def write_rows(self, path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({name: row.get(name) for name in fieldnames})
        return path
