from __future__ import annotations

import random
from datetime import date

from .config import MessageConfig


class MessageGenerator:
    def __init__(
        self,
        config: MessageConfig,
        *,
        rng: random.Random | None = None,
        today: date | None = None,
    ) -> None:
        self.config = config
        self.rng = rng or random.Random()
        self.today = today or date.today()
        self._used: set[str] = set()

    def render(self, name: str) -> str:
        values = {
            "name": name,
            "date": self.today.isoformat(),
            "emoji": self.rng.choice(self.config.emojis) if self.config.emojis else "",
            "phrase": self.rng.choice(self.config.phrases) if self.config.phrases else "",
        }

        for _ in range(20):
            template = self.rng.choice(self.config.templates)
            message = " ".join(template.format(**values).split())
            if message not in self._used:
                self._used.add(message)
                return message

        base = " ".join(self.config.templates[0].format(**values).split())
        suffix = 2
        candidate = f"{base} ({suffix})"
        while candidate in self._used:
            suffix += 1
            candidate = f"{base} ({suffix})"
        self._used.add(candidate)
        return candidate
