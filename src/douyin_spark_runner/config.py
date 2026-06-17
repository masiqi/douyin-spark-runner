from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class MessageConfig:
    templates: list[str] = field(default_factory=lambda: ["早呀 {name}，{phrase} {emoji}"])
    emojis: list[str] = field(default_factory=lambda: ["🙂", "✨", "🌿", "☀️"])
    phrases: list[str] = field(default_factory=lambda: ["路过打个招呼", "今天也顺顺利利", "补一下火花"])


@dataclass(slots=True)
class SleepConfig:
    min_seconds: float = 4.0
    max_seconds: float = 12.0


@dataclass(slots=True)
class RunnerConfig:
    max_recipients: int = 20
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    aliases: dict[str, str] = field(default_factory=dict)
    skip_groups: bool = True
    require_spark: bool = True
    state_dir: Path = Path("state")
    log_dir: Path = Path("logs")
    screenshot_dir: Path = Path("screenshots")
    browser_profile_dir: Path = Path("state/browser-profile")
    headless: bool = False
    slow_mo_ms: int = 50
    random_sleep: SleepConfig = field(default_factory=SleepConfig)
    messages: MessageConfig = field(default_factory=MessageConfig)


def load_config(path: Path | str = Path("config.yaml")) -> RunnerConfig:
    config_path = Path(path)
    raw: dict[str, Any] = {}
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if loaded is None:
            loaded = {}
        if not isinstance(loaded, dict):
            raise ValueError(f"{config_path} must contain a YAML mapping")
        raw = loaded

    config = RunnerConfig(
        max_recipients=int(raw.get("max_recipients", 20)),
        include=_string_list(raw.get("include", []), "include"),
        exclude=_string_list(raw.get("exclude", []), "exclude"),
        aliases=_string_dict(raw.get("aliases", {}), "aliases"),
        skip_groups=bool(raw.get("skip_groups", True)),
        require_spark=bool(raw.get("require_spark", True)),
        state_dir=Path(raw.get("state_dir", "state")),
        log_dir=Path(raw.get("log_dir", "logs")),
        screenshot_dir=Path(raw.get("screenshot_dir", "screenshots")),
        browser_profile_dir=Path(raw.get("browser_profile_dir", "state/browser-profile")),
        headless=bool(raw.get("headless", False)),
        slow_mo_ms=int(raw.get("slow_mo_ms", 50)),
        random_sleep=_sleep_config(raw.get("random_sleep", {})),
        messages=_message_config(raw.get("messages", {})),
    )
    if config.max_recipients < 1:
        raise ValueError("max_recipients must be at least 1")
    if config.random_sleep.min_seconds < 0 or config.random_sleep.max_seconds < 0:
        raise ValueError("random_sleep values must be non-negative")
    if config.random_sleep.min_seconds > config.random_sleep.max_seconds:
        raise ValueError("random_sleep.min_seconds cannot exceed max_seconds")
    return config


def _message_config(raw: Any) -> MessageConfig:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("messages must be a mapping")
    config = MessageConfig(
        templates=_string_list(raw.get("templates", MessageConfig().templates), "messages.templates"),
        emojis=_string_list(raw.get("emojis", MessageConfig().emojis), "messages.emojis"),
        phrases=_string_list(raw.get("phrases", MessageConfig().phrases), "messages.phrases"),
    )
    if not config.templates:
        raise ValueError("messages.templates must contain at least one template")
    return config


def _sleep_config(raw: Any) -> SleepConfig:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("random_sleep must be a mapping")
    return SleepConfig(
        min_seconds=float(raw.get("min_seconds", 4.0)),
        max_seconds=float(raw.get("max_seconds", 12.0)),
    )


def _string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    return value


def _string_dict(value: Any, field_name: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in value.items()
    ):
        raise ValueError(f"{field_name} must be a mapping of strings to strings")
    return dict(value)
