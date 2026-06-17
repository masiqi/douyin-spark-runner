from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


class DailyState:
    def __init__(self, state_dir: Path, *, today: date | None = None) -> None:
        self.state_dir = state_dir
        self.today = today or date.today()
        self.path = self.state_dir / "daily" / f"{self.today.isoformat()}.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"date": self.today.isoformat(), "sent": []}
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if "sent" not in data or not isinstance(data["sent"], list):
            data["sent"] = []
        return data

    def sent_names(self) -> set[str]:
        return {
            item["name"]
            for item in self.load().get("sent", [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }

    def record_sent(self, name: str, message: str, *, sent_at: datetime | None = None) -> None:
        sent_at = sent_at or datetime.now()
        data = self.load()
        data.setdefault("sent", []).append(
            {
                "name": name,
                "message": message,
                "sent_at": sent_at.isoformat(timespec="seconds"),
            }
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(self.path)
