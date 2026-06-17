import random
from datetime import date

from douyin_spark_runner.config import MessageConfig
from douyin_spark_runner.messages import MessageGenerator


def test_message_generator_varies_by_recipient_and_avoids_duplicates() -> None:
    config = MessageConfig(
        templates=[
            "早呀 {name}，{phrase} {emoji}",
            "{name} 今天也顺顺利利 {emoji}",
            "给 {name} 补个火花，{phrase}",
        ],
        emojis=["🙂", "✨", "🌿"],
        phrases=["今天状态不错", "路过打个招呼", "保持联系"],
    )
    generator = MessageGenerator(config, rng=random.Random(7), today=date(2026, 6, 17))

    messages = [generator.render(name) for name in ["阿明", "小李", "朋友"]]

    assert len(messages) == len(set(messages))
    assert all("{name}" not in message for message in messages)
    assert any("阿明" in message for message in messages)


def test_message_generator_falls_back_when_random_collision_happens() -> None:
    config = MessageConfig(templates=["嗨 {name} {date}"], emojis=["🙂"], phrases=["问候"])
    generator = MessageGenerator(config, rng=random.Random(1), today=date(2026, 6, 17))

    first = generator.render("同名")
    second = generator.render("同名")

    assert first == "嗨 同名 2026-06-17"
    assert second != first
    assert second.startswith("嗨 同名 2026-06-17")
