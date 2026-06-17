from douyin_spark_runner.contacts import Contact, detect_spark_text, has_spark
from douyin_spark_runner.config import RunnerConfig
from douyin_spark_runner.recipients import plan_recipients


def test_detect_spark_text_finds_fire_markers() -> None:
    assert detect_spark_text("张三", "互相关注 火花 18天") == "互相关注 火花 18天"
    assert has_spark("张三", "🔥 3") is True


def test_detect_spark_text_returns_empty_without_marker() -> None:
    assert detect_spark_text("张三", "普通最近消息") == ""
    assert has_spark("张三", "普通最近消息") is False


def test_require_spark_skips_non_spark_contacts() -> None:
    config = RunnerConfig(require_spark=True)
    decisions = plan_recipients(
        [
            Contact(name="有火花", selector_index=0, has_spark=True, spark_text="火花 9天"),
            Contact(name="普通好友", selector_index=1, has_spark=False),
        ],
        config,
        already_sent=set(),
        today=None,  # type: ignore[arg-type]
    )

    assert decisions[0].should_send is True
    assert decisions[0].reason == "eligible"
    assert decisions[1].should_send is False
    assert decisions[1].reason == "no_spark"
