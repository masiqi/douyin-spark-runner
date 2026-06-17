from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from .config import RunnerConfig
from .contacts import Contact


@dataclass(frozen=True, slots=True)
class RecipientDecision:
    contact: Contact
    should_send: bool
    reason: str


def plan_recipients(
    contacts: list[Contact],
    config: RunnerConfig,
    *,
    already_sent: set[str],
    today: date,
    force: bool = False,
) -> list[RecipientDecision]:
    del today
    decisions: list[RecipientDecision] = []
    selected_count = 0

    for contact in contacts:
        if config.include and not _matches_any(contact.name, config.include):
            decisions.append(RecipientDecision(contact, False, "not_in_include"))
            continue
        if _matches_any(contact.name, config.exclude):
            decisions.append(RecipientDecision(contact, False, "excluded"))
            continue
        if config.skip_groups and contact.is_group:
            decisions.append(RecipientDecision(contact, False, "group"))
            continue
        if not force and contact.name in already_sent:
            decisions.append(RecipientDecision(contact, False, "already_sent"))
            continue
        if selected_count >= config.max_recipients:
            decisions.append(RecipientDecision(contact, False, "max_recipients"))
            continue

        selected_count += 1
        decisions.append(RecipientDecision(contact, True, "eligible"))

    return decisions


def _matches_any(value: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if pattern in value:
            return True
        try:
            if re.search(pattern, value):
                return True
        except re.error:
            continue
    return False
