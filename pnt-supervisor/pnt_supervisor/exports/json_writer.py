"""JSON export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonWriter:
    """Write JSON-serializable dictionaries."""

    def write(self, path: Path, payload: dict[str, Any]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        return path
