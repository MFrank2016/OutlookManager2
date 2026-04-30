from __future__ import annotations

import json
from datetime import datetime, timezone

import database as db
import pytest
from dao.account_dao import AccountDAO
from models import AccountCredentials
from microsoft_access.capability_resolver import CapabilityResolver


class FakeAccountDAO:
    def __init__(self, *, persist_result: bool = True):
        self.updates: list[tuple[str, dict]] = []
        self.persist_result = persist_result

    def update_capability_snapshot(self, email: str, snapshot: dict) -> bool:
        self.updates.append((email, snapshot))
        return self.persist_result


async def graph_probe_available(_credentials: AccountCredentials) -> dict:
    return {
        "available": True,
        "access_token": "graph-token",
        "scope": "https://graph.microsoft.com/Mail.ReadWrite",
        "graph_available": True,
        "graph_read_available": True,
        "graph_write_available": True,
        "graph_send_available": False,
    }


async def graph_probe_unavailable(_credentials: AccountCredentials) -> dict:
    return {
        "available": False,
        "access_token": None,
        "scope": "",
        "mail_scope_granted": False,
        "graph_available": False,
        "graph_read_available": False,
        "graph_write_available": False,
        "graph_send_available": False,
    }


async def graph_probe_token_only(_credentials: AccountCredentials) -> dict:
    return {
        "available": None,
        "access_token": "graph-token",
        "scope": "https://graph.microsoft.com/.default",
        "graph_available": None,
        "graph_read_available": None,
        "graph_write_available": None,
        "graph_send_available": None,
    }


async def graph_probe_raises(_credentials: AccountCredentials) -> dict:
    raise RuntimeError("network down")


async def graph_probe_scope_confirmed(_credentials: AccountCredentials) -> dict:
    return {
        "available": True,
        "access_token": "graph-token",
        "scope": "Mail.Read offline_access",
        "graph_available": True,
        "graph_read_available": True,
        "graph_write_available": False,
        "graph_send_available": False,
    }


async def graph_probe_send_only(_credentials: AccountCredentials) -> dict:
    return {
        "available": True,
        "access_token": "graph-token",
        "scope": "Mail.Send offline_access",
        "graph_available": True,
        "graph_read_available": False,
        "graph_write_available": False,
        "graph_send_available": True,
    }


async def graph_probe_read_and_send(_credentials: AccountCredentials) -> dict:
    return {
        "available": True,
        "access_token": "graph-token",
        "scope": "Mail.Read Mail.Send offline_access",
        "graph_available": True,
        "graph_read_available": True,
        "graph_write_available": False,
        "graph_send_available": True,
    }


def test_detect_capability_prefers_graph_when_mail_scope_available():
    credentials = AccountCredentials(
        email="graph-capability@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    fixed_now = datetime(2026, 4, 30, 2, 3, 4, tzinfo=timezone.utc)
    dao = FakeAccountDAO()
    resolver = CapabilityResolver(
        graph_probe=graph_probe_available,
        account_dao=dao,
        now_fn=lambda: fixed_now,
    )

    snapshot = resolver.detect_capability_sync(credentials, persist=False)

    assert snapshot == {
        "graph_available": True,
        "graph_read_available": True,
        "graph_write_available": True,
        "graph_send_available": False,
        "imap_available": None,
        "recommended_provider": "graph_api",
        "last_probe_at": fixed_now.isoformat(),
        "last_probe_source": "graph_probe",
        "graph_probe_status": "mail_scope_confirmed",
    }
    assert dao.updates == []


def test_detect_capability_falls_back_to_imap_when_graph_unavailable():
    credentials = AccountCredentials(
        email="imap-capability@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    fixed_now = datetime(2026, 4, 30, 5, 6, 7, tzinfo=timezone.utc)
    resolver = CapabilityResolver(
        graph_probe=graph_probe_unavailable,
        account_dao=FakeAccountDAO(),
        now_fn=lambda: fixed_now,
    )

    snapshot = resolver.detect_capability_sync(credentials, persist=False)

    assert snapshot == {
        "graph_available": False,
        "graph_read_available": False,
        "graph_write_available": False,
        "graph_send_available": False,
        "imap_available": None,
        "recommended_provider": "imap",
        "last_probe_at": fixed_now.isoformat(),
        "last_probe_source": "graph_probe",
        "graph_probe_status": "confirmed_unavailable",
    }


def test_graph_token_only_does_not_prove_mail_capability():
    credentials = AccountCredentials(
        email="token-only@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    fixed_now = datetime(2026, 4, 30, 7, 8, 9, tzinfo=timezone.utc)
    resolver = CapabilityResolver(
        graph_probe=graph_probe_token_only,
        account_dao=FakeAccountDAO(),
        now_fn=lambda: fixed_now,
    )

    snapshot = resolver.detect_capability_sync(credentials, persist=False)

    assert snapshot == {
        "graph_available": None,
        "graph_read_available": None,
        "graph_write_available": None,
        "graph_send_available": None,
        "imap_available": None,
        "recommended_provider": None,
        "last_probe_at": fixed_now.isoformat(),
        "last_probe_source": "graph_probe",
        "graph_probe_status": "insufficient_evidence",
    }


def test_graph_probe_error_does_not_pretend_imap_is_confirmed():
    credentials = AccountCredentials(
        email="probe-error@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    fixed_now = datetime(2026, 4, 30, 7, 8, 10, tzinfo=timezone.utc)
    resolver = CapabilityResolver(
        graph_probe=graph_probe_raises,
        account_dao=FakeAccountDAO(),
        now_fn=lambda: fixed_now,
    )

    snapshot = resolver.detect_capability_sync(credentials, persist=False)

    assert snapshot == {
        "graph_available": None,
        "graph_read_available": None,
        "graph_write_available": None,
        "graph_send_available": None,
        "imap_available": None,
        "recommended_provider": None,
        "last_probe_at": fixed_now.isoformat(),
        "last_probe_source": "graph_probe",
        "graph_probe_status": "probe_error",
        "graph_probe_error": "network down",
    }


def test_send_only_graph_capability_does_not_recommend_graph_for_read_actions():
    credentials = AccountCredentials(
        email="send-only@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    fixed_now = datetime(2026, 4, 30, 7, 8, 11, tzinfo=timezone.utc)
    resolver = CapabilityResolver(
        graph_probe=graph_probe_send_only,
        account_dao=FakeAccountDAO(),
        now_fn=lambda: fixed_now,
    )

    snapshot = resolver.detect_capability_sync(credentials, persist=False)

    assert snapshot == {
        "graph_available": True,
        "graph_read_available": False,
        "graph_write_available": False,
        "graph_send_available": True,
        "imap_available": None,
        "recommended_provider": "imap",
        "last_probe_at": fixed_now.isoformat(),
        "last_probe_source": "graph_probe",
        "graph_probe_status": "mail_scope_confirmed",
    }


def test_read_and_send_graph_capability_keeps_graph_recommended():
    credentials = AccountCredentials(
        email="read-send@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    fixed_now = datetime(2026, 4, 30, 7, 8, 12, tzinfo=timezone.utc)
    resolver = CapabilityResolver(
        graph_probe=graph_probe_read_and_send,
        account_dao=FakeAccountDAO(),
        now_fn=lambda: fixed_now,
    )

    snapshot = resolver.detect_capability_sync(credentials, persist=False)

    assert snapshot == {
        "graph_available": True,
        "graph_read_available": True,
        "graph_write_available": False,
        "graph_send_available": True,
        "imap_available": None,
        "recommended_provider": "graph_api",
        "last_probe_at": fixed_now.isoformat(),
        "last_probe_source": "graph_probe",
        "graph_probe_status": "mail_scope_confirmed",
    }


def test_capability_snapshot_persisted_to_account_record(tmp_path, monkeypatch):
    db_file = tmp_path / "capability_snapshot.db"
    monkeypatch.setattr(db, "DB_TYPE", "sqlite")
    monkeypatch.setattr(db, "DB_FILE", str(db_file))
    monkeypatch.setattr(db, "_sqlite_last_integrity_check_ts", 0.0)

    db.init_database()
    dao = AccountDAO()
    dao.create(
        email="persisted-capability@example.com",
        refresh_token="rt",
        client_id="cid",
    )

    credentials = AccountCredentials(
        email="persisted-capability@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    fixed_now = datetime(2026, 4, 30, 8, 9, 10, tzinfo=timezone.utc)
    resolver = CapabilityResolver(
        graph_probe=graph_probe_scope_confirmed,
        account_dao=dao,
        now_fn=lambda: fixed_now,
    )

    snapshot = resolver.detect_capability_sync(credentials, persist=True)

    account = dao.get_by_email("persisted-capability@example.com")
    assert account is not None
    assert json.loads(account["capability_snapshot_json"]) == snapshot
    assert json.loads(credentials.capability_snapshot_json or "{}") == snapshot


def test_persist_true_raises_when_snapshot_write_fails():
    credentials = AccountCredentials(
        email="persist-fail@example.com",
        refresh_token="rt",
        client_id="cid",
    )
    resolver = CapabilityResolver(
        graph_probe=graph_probe_scope_confirmed,
        account_dao=FakeAccountDAO(persist_result=False),
    )

    with pytest.raises(RuntimeError, match="Failed to persist capability snapshot"):
        resolver.detect_capability_sync(credentials, persist=True)
