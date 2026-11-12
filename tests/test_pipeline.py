import sqlite3

from support_conversation.pipeline import run_pipeline


def test_redacts_and_builds_product(tmp_path):
    db = tmp_path / "support.sqlite3"
    result = run_pipeline([{"message_id": "1", "conversation_id": "c", "occurred_at": "2026-01-01T00:00:00Z", "channel": "chat", "author_type": "customer", "text": "mail a@example.com"}], db)
    assert result == {"accepted": 1, "rejected": 0, "duplicates": 0, "conversations": 1}
    with sqlite3.connect(db) as conn:
        text = conn.execute("select redacted_text from conversation_products").fetchone()[0]
        assert "a@example.com" not in text and "[EMAIL]" in text
