from __future__ import annotations

from fastapi.testclient import TestClient

import auth
from main import app
from models import AccountCredentials, EmailDetailsResponse, EmailItem, EmailListResponse


class FakeMailGateway:
    def __init__(self) -> None:
        self.list_calls: list[dict] = []
        self.detail_calls: list[dict] = []

    async def list_messages(self, credentials, **kwargs):
        self.list_calls.append({"email": credentials.email, **kwargs})
        return EmailListResponse(
            email_id=credentials.email,
            folder_view=kwargs["folder"],
            page=kwargs["page"],
            page_size=kwargs["page_size"],
            total_pages=1,
            total_emails=1,
            emails=[
                EmailItem(
                    message_id="msg-1",
                    folder="INBOX",
                    subject="Your code",
                    from_email="noreply@example.com",
                    date="2026-04-30T00:00:00",
                    sender_initial="N",
                )
            ],
        )

    async def get_message_detail(self, credentials, message_id: str, **kwargs):
        self.detail_calls.append(
            {
                "email": credentials.email,
                "message_id": message_id,
                **kwargs,
            }
        )
        return EmailDetailsResponse(
            message_id=message_id,
            subject="Your code",
            from_email="noreply@example.com",
            to_email=credentials.email,
            date="2026-04-30T00:00:00",
            body_plain="123456",
            verification_code="123456",
        )


async def _admin_override() -> dict:
    return {"username": "tester", "role": "admin", "is_active": True}


async def _load_credentials(email: str) -> AccountCredentials:
    return AccountCredentials(
        email=email,
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="auto",
    )


def test_v2_list_messages_supports_provider_override():
    gateway = FakeMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_loader = _load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v2/accounts/mailbox@example.com/messages",
                params={
                    "folder": "junk",
                    "page": 2,
                    "page_size": 50,
                    "override_provider": "graph",
                    "skip_cache": "true",
                    "subject_search": "code",
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert response.status_code == 200
    assert response.json()["email_id"] == "mailbox@example.com"
    assert gateway.list_calls == [
        {
            "email": "mailbox@example.com",
            "folder": "junk",
            "page": 2,
            "page_size": 50,
            "strategy_mode": "auto",
            "override_provider": "graph",
            "skip_cache": True,
            "sender_search": None,
            "subject_search": "code",
            "sort_by": "date",
            "sort_order": "desc",
            "start_time": None,
            "end_time": None,
        }
    ]


def test_v2_get_message_detail_reuses_mail_gateway():
    gateway = FakeMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_loader = _load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v2/accounts/mailbox@example.com/messages/msg-42",
                params={"override_provider": "imap", "skip_cache": "true"},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert response.status_code == 200
    assert response.json() == {
        "message_id": "msg-42",
        "subject": "Your code",
        "from_email": "noreply@example.com",
        "to_email": "mailbox@example.com",
        "date": "2026-04-30T00:00:00",
        "body_plain": "123456",
        "body_html": None,
        "verification_code": "123456",
    }
    assert gateway.detail_calls == [
        {
            "email": "mailbox@example.com",
            "message_id": "msg-42",
            "strategy_mode": "auto",
            "override_provider": "imap",
            "skip_cache": True,
        }
    ]


def test_v2_message_openapi_strategy_mode_uses_enum():
    app.openapi_schema = None
    schema = app.openapi()

    def _enum_refs(schema_fragment: dict) -> list[str]:
        refs: list[str] = []
        direct_ref = schema_fragment.get("$ref")
        if direct_ref:
            refs.append(direct_ref)
        for key in ("anyOf", "allOf", "oneOf"):
            for item in schema_fragment.get(key, []):
                ref = item.get("$ref")
                if ref:
                    refs.append(ref)
        return refs

    for path in (
        "/api/v2/accounts/{email}/messages",
        "/api/v2/accounts/{email}/messages/{message_id}",
    ):
        parameters = schema["paths"][path]["get"]["parameters"]
        strategy_mode_parameter = next(
            parameter for parameter in parameters if parameter["name"] == "strategy_mode"
        )
        assert any(
            ref.endswith("/StrategyMode")
            for ref in _enum_refs(strategy_mode_parameter["schema"])
        )



def test_v2_list_messages_rejects_invalid_strategy_mode():
    gateway = FakeMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_loader = _load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v2/accounts/mailbox@example.com/messages",
                params={"strategy_mode": "bogus_mode"},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert response.status_code == 422
    assert gateway.list_calls == []



def test_v2_get_message_detail_rejects_invalid_strategy_mode():
    gateway = FakeMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_loader = _load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v2/accounts/mailbox@example.com/messages/msg-42",
                params={"strategy_mode": "bogus_mode"},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert response.status_code == 422
    assert gateway.detail_calls == []



def test_v2_list_messages_rejects_invalid_provider_override():
    gateway = FakeMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_loader = _load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v2/accounts/mailbox@example.com/messages",
                params={"override_provider": "smtp"},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert response.status_code == 422
    assert gateway.list_calls == []


def test_v2_get_message_detail_rejects_invalid_provider_override():
    gateway = FakeMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_loader = _load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v2/accounts/mailbox@example.com/messages/msg-42",
                params={"override_provider": "smtp"},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert response.status_code == 422
    assert gateway.detail_calls == []
