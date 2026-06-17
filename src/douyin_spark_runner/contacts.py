from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Contact:
    name: str
    selector_index: int
    subtitle: str = ""
    is_group: bool = False
    has_spark: bool = False
    spark_text: str = ""


def looks_like_group(name: str, subtitle: str = "") -> bool:
    text = f"{name} {subtitle}"
    group_markers = ("群", "群聊", "人", "成员")
    return any(marker in text for marker in group_markers)


def detect_spark_text(name: str, subtitle: str = "") -> str:
    """Return a short spark marker when the contact row appears to show a Douyin spark/streak.

    Douyin's UI changes frequently, so this is intentionally heuristic. The
    caller should still use dry-run output to verify before real sends.
    """
    text = f"{name}\n{subtitle}"
    markers = ("火花", "🔥", "续火", "点亮", "已点亮")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if any(marker in line for marker in markers):
            return line[:80]
    return ""


def has_spark(name: str, subtitle: str = "") -> bool:
    return bool(detect_spark_text(name, subtitle))
