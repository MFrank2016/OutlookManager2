from fastapi.testclient import TestClient

from main import app
from routes import share_routes


def test_share_detail_accepts_mixed_naive_and_aware_datetimes(monkeypatch):
    app.dependency_overrides[share_routes.get_valid_share_token] = lambda: {
        "email_account_id": "mailbox@example.com",
        "start_time": "2026-05-02T09:00:00",
        "end_time": None,
        "subject_keyword": None,
        "sender_keyword": None,
        "is_active": True,
    }
    monkeypatch.setattr(
        share_routes.db,
        "get_cached_email_detail",
        lambda *_args, **_kwargs: {
            "message_id": "msg-1",
            "subject": "Verification code",
            "from_email": "noreply@example.com",
            "to_email": "mailbox@example.com",
            "date": "2026-05-02T01:30:00+00:00",
            "body_plain": "code",
            "body_html": None,
            "verification_code": "123456",
        },
    )

    try:
        with TestClient(app) as client:
            response = client.get("/share/test-token/emails/msg-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["message_id"] == "msg-1"
