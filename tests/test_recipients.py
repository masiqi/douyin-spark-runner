from datetime import date

from douyin_spark_runner.config import RunnerConfig
from douyin_spark_runner.contacts import Contact
from douyin_spark_runner.recipients import RecipientDecision, plan_recipients


def names(decisions: list[RecipientDecision]) -> list[str]:
    return [decision.contact.name for decision in decisions]


def test_plan_recipients_applies_include_exclude_groups_daily_and_cap() -> None:
    config = RunnerConfig(
        max_recipients=2,
        include=["阿", "小李"],
        exclude=["工作"],
        skip_groups=True,
        require_spark=False,
    )
    contacts = [
        Contact(name="阿明", selector_index=0),
        Contact(name="工作群", selector_index=1, is_group=True),
        Contact(name="小李", selector_index=2),
        Contact(name="小王", selector_index=3),
        Contact(name="阿芳", selector_index=4),
    ]

    decisions = plan_recipients(
        contacts,
        config,
        already_sent={"阿明"},
        today=date(2026, 6, 17),
        force=False,
    )

    eligible = [decision for decision in decisions if decision.should_send]
    skipped = {decision.contact.name: decision.reason for decision in decisions if not decision.should_send}

    assert names(eligible) == ["小李", "阿芳"]
    assert skipped["阿明"] == "already_sent"
    assert skipped["工作群"] == "not_in_include"
    assert skipped["小王"] == "not_in_include"


def test_plan_recipients_force_ignores_daily_state() -> None:
    config = RunnerConfig(max_recipients=10, require_spark=False)
    contacts = [Contact(name="阿明", selector_index=0)]

    decisions = plan_recipients(
        contacts,
        config,
        already_sent={"阿明"},
        today=date(2026, 6, 17),
        force=True,
    )

    assert decisions[0].should_send is True
