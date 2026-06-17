from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class JsonlLogger:
    def __init__(self, log_dir: Path, command: str) -> None:
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.path = log_dir / f"{timestamp}-{command}.jsonl"

    def write(self, event: str, **payload: Any) -> None:
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "event": event,
            **payload,
        }
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
