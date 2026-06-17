from datetime import date, datetime
from pathlib import Path

from douyin_spark_runner.state import DailyState


def test_daily_state_records_and_loads_sent_contacts(tmp_path: Path) -> None:
    daily = DailyState(tmp_path, today=date(2026, 6, 17))

    assert daily.sent_names() == set()

    daily.record_sent("阿明", "早呀", sent_at=datetime(2026, 6, 17, 9, 30, 0))
    reloaded = DailyState(tmp_path, today=date(2026, 6, 17))

    assert reloaded.sent_names() == {"阿明"}
    data = reloaded.load()
    assert data["date"] == "2026-06-17"
    assert data["sent"][0]["name"] == "阿明"
    assert data["sent"][0]["message"] == "早呀"
