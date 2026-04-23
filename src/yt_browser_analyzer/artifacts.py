from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .timeutil import utc_now


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_run_dir(output_root: Path, video_id: str) -> Path:
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    return output_root / video_id / f"{video_id}-{stamp}"
