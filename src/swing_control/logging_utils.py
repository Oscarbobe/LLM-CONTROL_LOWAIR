"""JSONL logging helpers for Swing control runs."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class JsonlRunLogger:
    """Append structured run events to a JSON Lines file."""

    def __init__(
        self,
        log_dir: str | Path = "data/logs",
        *,
        prefix: str = "swing_run",
        run_type: str = "unknown",
    ) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.run_type = run_type
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.path = self.log_dir / f"{prefix}_{stamp}.jsonl"

    def log(self, event: str, **fields: Any) -> None:
        payload = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "run_type": self.run_type,
            "event": event,
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(_jsonable(payload), ensure_ascii=False) + "\n")

    def finish(self, exit_code: int, **fields: Any) -> None:
        self.log("run_finished", exit_code=exit_code, **fields)


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
