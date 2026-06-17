from pathlib import Path

from douyin_spark_runner.config import load_config


def test_load_config_applies_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
max_recipients: 3
exclude:
  - 老板
messages:
  templates:
    - "早呀 {name} {emoji}"
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.max_recipients == 3
    assert config.exclude == ["老板"]
    assert config.include == []
    assert config.aliases == {}
    assert config.skip_groups is True
    assert config.state_dir == Path("state")
    assert config.messages.templates == ["早呀 {name} {emoji}"]
    assert config.messages.emojis


def test_load_config_parses_aliases(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
aliases:
  疯狂的兔子: 三儿
  张三的抖音昵称: 张三
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.aliases == {"疯狂的兔子": "三儿", "张三的抖音昵称": "张三"}


def test_load_config_rejects_missing_message_templates(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("messages:\n  templates: []\n", encoding="utf-8")

    try:
        load_config(config_path)
    except ValueError as exc:
        assert "messages.templates" in str(exc)
    else:
        raise AssertionError("expected ValueError")
