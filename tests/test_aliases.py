from dataclasses import dataclass

from douyin_spark_runner.cli import _message_plan
from douyin_spark_runner.contacts import Contact
from douyin_spark_runner.recipients import RecipientDecision


@dataclass
class FakeGenerator:
    seen: list[str]

    def render(self, name: str) -> str:
        self.seen.append(name)
        return f"你好 {name}"


def test_message_plan_uses_alias_for_message_but_keeps_contact_name() -> None:
    contact = Contact(name="疯狂的兔子", selector_index=0)
    decision = RecipientDecision(contact=contact, should_send=True, reason="eligible")
    generator = FakeGenerator(seen=[])

    plan = _message_plan([decision], generator, {"疯狂的兔子": "三儿"})

    assert generator.seen == ["三儿"]
    assert plan[0]["name"] == "疯狂的兔子"
    assert plan[0]["display_name"] == "三儿"
    assert plan[0]["message"] == "你好 三儿"


def test_message_plan_falls_back_to_contact_name_without_alias() -> None:
    contact = Contact(name="张三", selector_index=0)
    decision = RecipientDecision(contact=contact, should_send=True, reason="eligible")
    generator = FakeGenerator(seen=[])

    plan = _message_plan([decision], generator, {})

    assert generator.seen == ["张三"]
    assert plan[0]["display_name"] == "张三"
    assert plan[0]["message"] == "你好 张三"
