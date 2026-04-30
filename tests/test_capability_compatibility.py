from __future__ import annotations

import email_service
import oauth_service
from models import AccountCredentials


async def _send_only_probe(_credentials: AccountCredentials) -> dict:
    return {
        "available": True,
        "mail_scope_granted": True,
        "graph_available": True,
        "graph_read_available": False,
        "graph_write_available": False,
        "graph_send_available": True,
        "availability_status": "mail_scope_confirmed",
        "scope": "Mail.Send offline_access",
        "evidence": "jwt_claims",
    }


async def _read_probe(_credentials: AccountCredentials) -> dict:
    return {
        "available": True,
        "mail_scope_granted": True,
        "graph_available": True,
        "graph_read_available": True,
        "graph_write_available": False,
        "graph_send_available": True,
        "availability_status": "mail_scope_confirmed",
        "scope": "Mail.Read Mail.Send offline_access",
        "evidence": "jwt_claims",
    }


async def _unknown_probe(_credentials: AccountCredentials) -> dict:
    return {
        "available": None,
        "mail_scope_granted": None,
        "graph_available": None,
        "graph_read_available": None,
        "graph_write_available": None,
        "graph_send_available": None,
        "availability_status": "insufficient_evidence",
        "scope": "",
        "evidence": "token_only",
    }


async def _probe_error(_credentials: AccountCredentials) -> dict:
    return {
        "available": None,
        "mail_scope_granted": None,
        "graph_available": None,
        "graph_read_available": None,
        "graph_write_available": None,
        "graph_send_available": None,
        "availability_status": "probe_error",
        "scope": "",
        "evidence": "probe_error",
        "error_category": "probe_error",
        "error": "network down",
    }


class FakeDB:
    def __init__(self):
        self.updates: list[tuple[str, dict]] = []

    def update_account(self, email: str, **kwargs) -> bool:
        self.updates.append((email, kwargs))
        return True


async def test_detect_and_update_api_method_keeps_imap_for_send_only_probe(monkeypatch):
    credentials = AccountCredentials(
        email="send-only-default@example.com",
        refresh_token="rt",
        client_id="cid",
        api_method="",
    )
    fake_db = FakeDB()

    import graph_api_service

    monkeypatch.setattr(graph_api_service, "check_graph_api_availability", _send_only_probe)
    monkeypatch.setattr(oauth_service, "db", fake_db)

    result = await oauth_service.detect_and_update_api_method(credentials)

    assert result == "imap"
    assert fake_db.updates == [
        (credentials.email, {"api_method": "imap"})
    ]


async def test_detect_and_update_api_method_unknown_probe_does_not_persist_imap(monkeypatch):
    credentials = AccountCredentials(
        email="unknown-default@example.com",
        refresh_token="rt",
        client_id="cid",
        api_method="",
    )
    fake_db = FakeDB()

    import graph_api_service

    monkeypatch.setattr(graph_api_service, "check_graph_api_availability", _unknown_probe)
    monkeypatch.setattr(oauth_service, "db", fake_db)

    result = await oauth_service.detect_and_update_api_method(credentials)

    assert result == "imap"
    assert fake_db.updates == []


async def test_detect_and_update_api_method_probe_error_does_not_persist_imap(monkeypatch):
    credentials = AccountCredentials(
        email="probe-error-default@example.com",
        refresh_token="rt",
        client_id="cid",
        api_method="",
    )
    fake_db = FakeDB()

    import graph_api_service

    monkeypatch.setattr(graph_api_service, "check_graph_api_availability", _probe_error)
    monkeypatch.setattr(oauth_service, "db", fake_db)

    result = await oauth_service.detect_and_update_api_method(credentials)

    assert result == "imap"
    assert fake_db.updates == []


def test_email_service_read_route_guard_rejects_send_only_probe():
    probe_result = {
        "available": True,
        "graph_available": True,
        "graph_read_available": False,
        "graph_write_available": False,
        "graph_send_available": True,
        "scope": "Mail.Send offline_access",
    }

    assert email_service._should_use_graph_api_for_read_probe(probe_result) is False


def test_email_service_read_route_guard_accepts_read_capable_probe():
    probe_result = {
        "available": True,
        "graph_available": True,
        "graph_read_available": True,
        "graph_write_available": False,
        "graph_send_available": True,
        "scope": "Mail.Read Mail.Send offline_access",
    }

    assert email_service._should_use_graph_api_for_read_probe(probe_result) is True


def test_email_service_unknown_probe_falls_back_without_persisting():
    fake_db = FakeDB()
    use_graph_api = email_service._resolve_graph_read_probe_choice(
        email="unknown-read-route@example.com",
        probe_result={
            "available": None,
            "graph_available": None,
            "graph_read_available": None,
            "graph_write_available": None,
            "graph_send_available": None,
            "availability_status": "insufficient_evidence",
            "scope": "",
        },
        db_module=fake_db,
    )

    assert use_graph_api is False
    assert fake_db.updates == []


def test_email_service_probe_error_falls_back_without_persisting():
    fake_db = FakeDB()
    use_graph_api = email_service._resolve_graph_read_probe_choice(
        email="probe-error-read-route@example.com",
        probe_result={
            "available": None,
            "graph_available": None,
            "graph_read_available": None,
            "graph_write_available": None,
            "graph_send_available": None,
            "availability_status": "probe_error",
            "scope": "",
        },
        db_module=fake_db,
    )

    assert use_graph_api is False
    assert fake_db.updates == []
