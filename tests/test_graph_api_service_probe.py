from __future__ import annotations

import base64
import json

import pytest

import graph_api_service
from microsoft_access import AccessTokenResult
from models import AccountCredentials


class FakeBroker:
    def __init__(self, *, result: AccessTokenResult | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls: list[dict] = []

    async def fetch_access_token(self, credentials, *, persist, requested_provider):
        self.calls.append(
            {
                "email": credentials.email,
                "persist": persist,
                "requested_provider": requested_provider,
            }
        )
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def credentials() -> AccountCredentials:
    return AccountCredentials(
        email="graph-probe@example.com",
        refresh_token="rt",
        client_id="cid",
    )


def _build_jwt(payload: dict) -> str:
    def _b64(data: dict) -> str:
        raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    return f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64(payload)}.sig"


@pytest.mark.asyncio
async def test_probe_confirms_mail_scope_from_scp(monkeypatch, credentials):
    token = _build_jwt({"scp": "openid profile Mail.Read offline_access"})
    broker = FakeBroker(
        result=AccessTokenResult(
            access_token=token,
            expires_at="2026-04-30T00:00:00+00:00",
            expires_in=3600,
            provider_hint="graph_api",
        )
    )
    monkeypatch.setattr(graph_api_service, "TokenBroker", lambda: broker)

    result = await graph_api_service.check_graph_api_availability(credentials)

    assert result == {
        "available": True,
        "access_token": token,
        "scope": "openid profile Mail.Read offline_access",
        "mail_scope_granted": True,
        "graph_available": True,
        "graph_read_available": True,
        "graph_write_available": False,
        "graph_send_available": False,
        "availability_status": "mail_scope_confirmed",
        "evidence": "jwt_claims",
    }


@pytest.mark.asyncio
async def test_probe_confirms_mail_scope_from_roles(monkeypatch, credentials):
    token = _build_jwt({"roles": ["User.Read", "Mail.ReadWrite"]})
    broker = FakeBroker(
        result=AccessTokenResult(
            access_token=token,
            expires_at="2026-04-30T00:00:00+00:00",
            expires_in=3600,
            provider_hint="graph_api",
        )
    )
    monkeypatch.setattr(graph_api_service, "TokenBroker", lambda: broker)

    result = await graph_api_service.check_graph_api_availability(credentials)

    assert result["available"] is True
    assert result["mail_scope_granted"] is True
    assert result["graph_available"] is True
    assert result["graph_read_available"] is True
    assert result["graph_write_available"] is True
    assert result["graph_send_available"] is False
    assert result["availability_status"] == "mail_scope_confirmed"
    assert result["evidence"] == "jwt_claims"
    assert result["scope"] == "User.Read Mail.ReadWrite"


@pytest.mark.asyncio
async def test_probe_reports_confirmed_unavailable_for_non_mail_scope(monkeypatch, credentials):
    token = _build_jwt({"scp": "openid profile Files.Read"})
    broker = FakeBroker(
        result=AccessTokenResult(
            access_token=token,
            expires_at="2026-04-30T00:00:00+00:00",
            expires_in=3600,
            provider_hint="graph_api",
        )
    )
    monkeypatch.setattr(graph_api_service, "TokenBroker", lambda: broker)

    result = await graph_api_service.check_graph_api_availability(credentials)

    assert result["available"] is False
    assert result["mail_scope_granted"] is False
    assert result["graph_available"] is False
    assert result["graph_read_available"] is False
    assert result["graph_write_available"] is False
    assert result["graph_send_available"] is False
    assert result["availability_status"] == "confirmed_unavailable"
    assert result["evidence"] == "jwt_claims"
    assert result["scope"] == "openid profile Files.Read"


@pytest.mark.asyncio
async def test_probe_detects_send_only_scope(monkeypatch, credentials):
    token = _build_jwt({"scp": "Mail.Send offline_access"})
    broker = FakeBroker(
        result=AccessTokenResult(
            access_token=token,
            expires_at="2026-04-30T00:00:00+00:00",
            expires_in=3600,
            provider_hint="graph_api",
        )
    )
    monkeypatch.setattr(graph_api_service, "TokenBroker", lambda: broker)

    result = await graph_api_service.check_graph_api_availability(credentials)

    assert result["available"] is True
    assert result["mail_scope_granted"] is True
    assert result["graph_available"] is True
    assert result["graph_read_available"] is False
    assert result["graph_write_available"] is False
    assert result["graph_send_available"] is True
    assert result["availability_status"] == "mail_scope_confirmed"
    assert result["scope"] == "Mail.Send offline_access"


@pytest.mark.asyncio
async def test_probe_detects_read_and_send_scope(monkeypatch, credentials):
    token = _build_jwt({"scp": "Mail.Read Mail.Send"})
    broker = FakeBroker(
        result=AccessTokenResult(
            access_token=token,
            expires_at="2026-04-30T00:00:00+00:00",
            expires_in=3600,
            provider_hint="graph_api",
        )
    )
    monkeypatch.setattr(graph_api_service, "TokenBroker", lambda: broker)

    result = await graph_api_service.check_graph_api_availability(credentials)

    assert result["available"] is True
    assert result["mail_scope_granted"] is True
    assert result["graph_available"] is True
    assert result["graph_read_available"] is True
    assert result["graph_write_available"] is False
    assert result["graph_send_available"] is True
    assert result["availability_status"] == "mail_scope_confirmed"
    assert result["scope"] == "Mail.Read Mail.Send"


@pytest.mark.asyncio
async def test_probe_reports_insufficient_evidence_for_non_jwt_token(monkeypatch, credentials):
    broker = FakeBroker(
        result=AccessTokenResult(
            access_token="not-a-jwt",
            expires_at="2026-04-30T00:00:00+00:00",
            expires_in=3600,
            provider_hint="graph_api",
        )
    )
    monkeypatch.setattr(graph_api_service, "TokenBroker", lambda: broker)

    result = await graph_api_service.check_graph_api_availability(credentials)

    assert result == {
        "available": None,
        "access_token": "not-a-jwt",
        "scope": "",
        "mail_scope_granted": None,
        "graph_available": None,
        "graph_read_available": None,
        "graph_write_available": None,
        "graph_send_available": None,
        "availability_status": "insufficient_evidence",
        "evidence": "token_only",
    }


@pytest.mark.asyncio
async def test_probe_reports_probe_error_when_broker_raises(monkeypatch, credentials):
    broker = FakeBroker(error=RuntimeError("broker down"))
    monkeypatch.setattr(graph_api_service, "TokenBroker", lambda: broker)

    result = await graph_api_service.check_graph_api_availability(credentials)

    assert result == {
        "available": None,
        "access_token": None,
        "scope": "",
        "mail_scope_granted": None,
        "graph_available": None,
        "graph_read_available": None,
        "graph_write_available": None,
        "graph_send_available": None,
        "availability_status": "probe_error",
        "evidence": "probe_error",
        "error_category": "probe_error",
        "error": "broker down",
    }
