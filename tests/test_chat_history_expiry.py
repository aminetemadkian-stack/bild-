from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.services import storage


@pytest.fixture
def isolated_history_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "history-test.db"))
    storage.init_db()
    return tmp_path


def test_saved_messages_expire_after_configured_retention(isolated_history_db):
    start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    storage.save_chat_exchange("hello", "hi", retention_days=3, now=start)

    # Before the deadline, both messages remain. At the exact deadline they expire.
    assert len(storage.list_chat_history(now=start + timedelta(days=2))) == 2
    deleted = storage.cleanup_chat_history(now=start + timedelta(days=3))
    assert deleted == 2
    assert storage.list_chat_history(now=start + timedelta(days=3)) == []


def test_cleanup_removes_only_expired_messages(isolated_history_db):
    now = datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc)
    storage.save_chat_exchange("old question", "old answer", 1, now=now - timedelta(days=2))
    storage.save_chat_exchange("fresh question", "fresh answer", 5, now=now)

    deleted = storage.cleanup_chat_history(now=now)

    assert deleted == 2
    messages = storage.list_chat_history(now=now)
    assert [m["content"] for m in messages] == ["fresh question", "fresh answer"]


def test_read_history_automatically_cleans_expired_rows(isolated_history_db):
    now = datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)
    storage.save_chat_exchange("expired", "expired reply", 1, now=now - timedelta(days=2))
    storage.save_chat_exchange("current", "current reply", 10, now=now)

    result = storage.list_chat_history(now=now)

    assert [m["content"] for m in result] == ["current", "current reply"]


def test_history_is_bounded_to_500_rows(isolated_history_db):
    now = datetime(2026, 4, 1, tzinfo=timezone.utc)
    for i in range(251):
        storage.save_chat_exchange(f"q{i}", f"a{i}", 30, now=now + timedelta(seconds=i))

    messages = storage.list_chat_history(limit=500, now=now + timedelta(seconds=250))

    assert len(messages) == 500
    assert messages[0]["content"] == "q1"
    assert messages[-1]["content"] == "a250"


def test_cleanup_returns_zero_when_nothing_expired(isolated_history_db):
    now = datetime(2026, 5, 1, tzinfo=timezone.utc)
    storage.save_chat_exchange("still here", "still here", 2, now=now)

    assert storage.cleanup_chat_history(now=now + timedelta(days=1)) == 0
    assert len(storage.list_chat_history(now=now + timedelta(days=1))) == 2


def test_user_can_delete_one_message_without_deleting_the_rest(isolated_history_db):
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    storage.save_chat_exchange("question", "answer", 30, now=now)
    messages = storage.list_chat_history(now=now)
    user_message_id = messages[0]["id"]

    assert storage.delete_chat_message(user_message_id) is True
    assert storage.delete_chat_message(user_message_id) is False
    remaining = storage.list_chat_history(now=now)
    assert [m["content"] for m in remaining] == ["answer"]
