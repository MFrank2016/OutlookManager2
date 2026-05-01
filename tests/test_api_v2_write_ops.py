from __future__ import annotations

from fastapi.testclient import TestClient

import auth
from main import app
from models import AccountCredentials


class FakeWriteLifecycleService:
    def __init__(self) -> None:
        self.register_calls: list[dict] = []
        self.import_calls: list[dict] = []
        self.refresh_calls: list[str] = []

    async def register_account(self, credentials: AccountCredentials):
        self.register_calls.append(
            {
                "email": credentials.email,
                "strategy_mode": credentials.strategy_mode,
                "lifecycle_state": credentials.lifecycle_state,
                "capability_snapshot_json": credentials.capability_snapshot_json,
                "provider_health_json": credentials.provider_health_json,
            }
        )
        return {
            "email_id": credentials.email,
            "message": "Account verified and saved successfully.",
        }

    async def import_accounts(
        self,
        items,
        *,
        mode: str,
        api_method: str,
        tags: list[str],
    ):
        self.import_calls.append(
            {
                "mode": mode,
                "api_method": api_method,
                "tags": tags,
                "emails": [item.email for item in items],
            }
        )
        persisted_count = 0 if mode == "dry_run" else len(items)
        return {
            "mode": mode,
            "total_count": len(items),
            "success_count": len(items),
            "failed_count": 0,
            "persisted_count": persisted_count,
            "results": [
                {
                    "email": item.email,
                    "success": True,
                    "persisted": mode == "commit",
                    "message": "ok",
                }
                for item in items
            ],
        }

    async def refresh_account_token(self, email: str):
        self.refresh_calls.append(email)
        return {
            "success": True,
            "email_id": email,
            "message": "Token refreshed successfully at 2026-04-30T00:00:00+00:00",
        }


class FakeWriteMailGateway:
    def __init__(self) -> None:
        self.delete_calls: list[dict] = []
        self.batch_delete_calls: list[dict] = []
        self.send_calls: list[dict] = []

    async def delete_message(self, credentials, message_id: str, **kwargs):
        self.delete_calls.append(
            {
                "email": credentials.email,
                "message_id": message_id,
                **kwargs,
            }
        )
        return True

    async def delete_messages_batch(self, credentials, *, folder: str, **kwargs):
        self.batch_delete_calls.append(
            {
                "email": credentials.email,
                "folder": folder,
                **kwargs,
            }
        )
        return {
            "success_count": 3,
            "fail_count": 1,
            "total_count": 4,
        }

    async def send_message(self, credentials, *, to: str, subject: str, body_text=None, body_html=None, **kwargs):
        self.send_calls.append(
            {
                "email": credentials.email,
                "to": to,
                "subject": subject,
                "body_text": body_text,
                "body_html": body_html,
                **kwargs,
            }
        )
        return "msg-sent-1"


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


def test_v2_register_persists_strategy_and_health():
    service = FakeWriteLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts",
                json={
                    "email": "writer@example.com",
                    "refresh_token": "refresh-token",
                    "client_id": "client-id",
                    "strategy_mode": "graph_preferred",
                    "lifecycle_state": "healthy",
                    "capability_snapshot_json": "{\"recommended_provider\":\"graph_api\"}",
                    "provider_health_json": "{\"last_error_message\":\"none\"}",
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json() == {
        "email_id": "writer@example.com",
        "message": "Account verified and saved successfully.",
    }
    assert service.register_calls == [
        {
            "email": "writer@example.com",
            "strategy_mode": "graph_preferred",
            "lifecycle_state": "healthy",
            "capability_snapshot_json": "{\"recommended_provider\":\"graph_api\"}",
            "provider_health_json": "{\"last_error_message\":\"none\"}",
        }
    ]


def test_v2_import_dry_run_does_not_create_accounts():
    service = FakeWriteLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/import",
                params={"mode": "dry_run"},
                json={
                    "items": [
                        {
                            "email": "dry-run@example.com",
                            "refresh_token": "refresh-token",
                            "client_id": "client-id",
                        }
                    ],
                    "api_method": "graph",
                    "tags": ["seed"],
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json()["mode"] == "dry_run"
    assert response.json()["persisted_count"] == 0
    assert service.import_calls == [
        {
            "mode": "dry_run",
            "api_method": "graph",
            "tags": ["seed"],
            "emails": ["dry-run@example.com"],
        }
    ]


def test_v2_import_commit_creates_accounts():
    service = FakeWriteLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/import",
                params={"mode": "commit"},
                json={
                    "items": [
                        {
                            "email": "one@example.com",
                            "refresh_token": "refresh-token-1",
                            "client_id": "client-id-1",
                        },
                        {
                            "email": "two@example.com",
                            "refresh_token": "refresh-token-2",
                            "client_id": "client-id-2",
                        },
                    ],
                    "api_method": "imap",
                    "tags": ["batch"],
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json()["mode"] == "commit"
    assert response.json()["persisted_count"] == 2
    assert service.import_calls == [
        {
            "mode": "commit",
            "api_method": "imap",
            "tags": ["batch"],
            "emails": ["one@example.com", "two@example.com"],
        }
    ]


def test_v2_token_refresh_reuses_lifecycle_service():
    service = FakeWriteLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post("/api/v2/accounts/fresh@example.com/token-refresh")
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json() == {
        "email_id": "fresh@example.com",
        "message": "Token refreshed successfully at 2026-04-30T00:00:00+00:00",
    }
    assert service.refresh_calls == ["fresh@example.com"]


def test_v2_delete_and_send_reuse_mail_gateway():
    gateway = FakeWriteMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_loader = _load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            delete_response = client.delete("/api/v2/accounts/mailbox@example.com/messages/msg-42")
            batch_delete_response = client.delete(
                "/api/v2/accounts/mailbox@example.com/messages",
                params={"folder": "junk"},
            )
            send_response = client.post(
                "/api/v2/accounts/mailbox@example.com/messages/send",
                json={
                    "to": "target@example.com",
                    "subject": "hello",
                    "body_text": "plain",
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "success": True,
        "message": "Email deleted successfully",
        "message_id": "msg-42",
    }
    assert batch_delete_response.status_code == 200
    assert batch_delete_response.json() == {
        "success": True,
        "message": "Successfully deleted 3 emails, 1 failed",
        "success_count": 3,
        "fail_count": 1,
        "total_count": 4,
    }
    assert send_response.status_code == 200
    assert send_response.json() == {
        "success": True,
        "message": "Email sent successfully",
        "message_id": "msg-sent-1",
    }
    assert gateway.delete_calls == [
        {
            "email": "mailbox@example.com",
            "message_id": "msg-42",
            "strategy_mode": "auto",
            "override_provider": None,
        }
    ]
    assert gateway.batch_delete_calls == [
        {
            "email": "mailbox@example.com",
            "folder": "junk",
            "strategy_mode": "auto",
            "override_provider": None,
        }
    ]
    assert gateway.send_calls == [
        {
            "email": "mailbox@example.com",
            "to": "target@example.com",
            "subject": "hello",
            "body_text": "plain",
            "body_html": None,
            "strategy_mode": "auto",
            "override_provider": None,
        }
    ]
