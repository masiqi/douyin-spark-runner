from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Contact:
    name: str
    selector_index: int
    subtitle: str = ""
    is_group: bool = False


def looks_like_group(name: str, subtitle: str = "") -> bool:
    text = f"{name} {subtitle}"
    group_markers = ("群", "群聊", "人", "成员")
    return any(marker in text for marker in group_markers)
