from __future__ import annotations

import json

import pytest

from fastapi.testclient import TestClient

import account_service
import auth
from main import app
from models import AccountCredentials, EmailDetailsResponse, EmailItem, EmailListResponse
from microsoft_access.account_lifecycle_service import AccountLifecycleService
from microsoft_access.mail_gateway import MailGateway


class FakeLifecycleService:
    def __init__(self) -> None:
        self.probe_calls: list[dict] = []
        self.health_calls: list[str] = []
        self.capability_calls: list[dict] = []

    async def probe_account(self, credentials, *, persist: bool = False):
        self.probe_calls.append({"email": credentials.email, "persist": persist})
        return {
            "token_ok": True,
            "capability": {
                "graph_available": True,
                "graph_read_available": True,
                "graph_write_available": False,
                "graph_send_available": False,
                "imap_available": None,
                "recommended_provider": "graph_api",
            },
            "lifecycle_state": "probed",
            "warnings": [],
        }

    async def get_account_health(self, email: str):
        self.health_calls.append(email)
        return {
            "email": email,
            "strategy_mode": "graph_preferred",
            "lifecycle_state": "healthy",
            "capability": {
                "graph_available": True,
                "graph_read_available": False,
                "graph_write_available": False,
                "graph_send_available": True,
                "imap_available": None,
                "recommended_provider": "imap",
            },
            "last_provider_used": "imap",
            "last_error": {
                "code": "GRAPH_TIMEOUT",
                "message": "graph timeout",
            },
        }

    async def detect_capability(self, email: str, *, persist: bool = True):
        self.capability_calls.append({"email": email, "persist": persist})
        return {
            "graph_available": True,
            "graph_read_available": True,
            "graph_write_available": False,
            "graph_send_available": False,
            "imap_available": None,
            "recommended_provider": "graph_api",
            "last_probe_at": "2026-04-30T00:00:00+00:00",
            "last_probe_source": "api_v2_capability_detection",
            "graph_probe_status": "mail_scope_confirmed",
        }


class FakeProvider:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[tuple[str, dict]] = []

    async def list_messages(self, credentials: AccountCredentials, **kwargs):
        self.calls.append(("list", {"email": credentials.email, **kwargs}))
        return EmailListResponse(
            email_id=credentials.email,
            folder_view=kwargs["folder"],
            page=kwargs["page"],
            page_size=kwargs["page_size"],
            total_pages=1,
            total_emails=1,
            emails=[
                EmailItem(
                    message_id=f"{self.name}-msg-1",
                    folder="INBOX",
                    subject=f"from-{self.name}",
                    from_email="noreply@example.com",
                    date="2026-04-30T00:00:00",
                    sender_initial="N",
                )
            ],
        )

    async def get_message_detail(self, credentials: AccountCredentials, message_id: str, **kwargs):
        self.calls.append(
            ("detail", {"email": credentials.email, "message_id": message_id, **kwargs})
        )
        return EmailDetailsResponse(
            message_id=message_id,
            subject=f"from-{self.name}",
            from_email="noreply@example.com",
            to_email=credentials.email,
            date="2026-04-30T00:00:00",
            body_plain="123456",
            verification_code="123456",
        )


async def _admin_override() -> dict:
    return {"username": "tester", "role": "admin", "is_active": True}


async def _non_admin_override() -> dict:
    return {
        "username": "normal-user",
        "role": "user",
        "is_active": True,
        "bound_accounts": ["mailbox@example.com"],
        "permissions": ["view_emails"],
    }


def test_probe_account_returns_capability_without_persisting():
    service = FakeLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/probe",
                json={
                    "email": "probe@example.com",
                    "refresh_token": "refresh-token",
                    "client_id": "client-id",
                    "strategy_mode": "auto",
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json() == {
        "token_ok": True,
        "capability": {
            "graph_available": True,
            "graph_read_available": True,
            "graph_write_available": False,
            "graph_send_available": False,
            "imap_available": None,
            "recommended_provider": "graph_api",
        },
        "lifecycle_state": "probed",
        "warnings": [],
    }
    assert service.probe_calls == [{"email": "probe@example.com", "persist": False}]


def test_probe_account_requires_admin():
    service = FakeLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _non_admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/probe",
                json={
                    "email": "probe@example.com",
                    "refresh_token": "refresh-token",
                    "client_id": "client-id",
                    "strategy_mode": "auto",
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 403
    assert service.probe_calls == []


def test_get_account_health_returns_strategy_capability_and_last_error():
    service = FakeLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.get("/api/v2/accounts/health@example.com/health")
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json() == {
        "email": "health@example.com",
        "strategy_mode": "graph_preferred",
        "lifecycle_state": "healthy",
        "capability": {
            "graph_available": True,
            "graph_read_available": False,
            "graph_write_available": False,
            "graph_send_available": True,
            "imap_available": None,
            "recommended_provider": "imap",
        },
        "last_provider_used": "imap",
        "last_error": {
            "code": "GRAPH_TIMEOUT",
            "message": "graph timeout",
        },
    }
    assert service.health_calls == ["health@example.com"]


def test_account_v2_openapi_schemas_are_explicit():
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

    expected_paths = {
        "/api/v2/accounts/probe": "post",
        "/api/v2/accounts/{email}/health": "get",
        "/api/v2/accounts/{email}/capability-detection": "post",
        "/api/v2/accounts/{email}/delivery-strategy": "get",
        "/api/v2/accounts/{email}/delivery-strategy/override": "post",
    }

    for path, method in expected_paths.items():
        operation = schema["paths"][path][method]
        response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema != {}, f"{method.upper()} {path} response schema should not be empty"
        assert response_schema.get("$ref") or response_schema.get("properties")

    delivery_strategy_parameters = schema["paths"]["/api/v2/accounts/{email}/delivery-strategy"]["get"]["parameters"]
    strategy_mode_parameter = next(
        parameter for parameter in delivery_strategy_parameters if parameter["name"] == "strategy_mode"
    )
    strategy_mode_schema = strategy_mode_parameter["schema"]
    assert any(ref.endswith("/StrategyMode") for ref in _enum_refs(strategy_mode_schema))

    probe_strategy_mode_schema = schema["components"]["schemas"]["AccountCredentials"]["properties"]["strategy_mode"]
    assert any(ref.endswith("/StrategyMode") for ref in _enum_refs(probe_strategy_mode_schema))

    account_info_strategy_mode_schema = schema["components"]["schemas"]["AccountInfo"]["properties"]["strategy_mode"]
    assert any(ref.endswith("/StrategyMode") for ref in _enum_refs(account_info_strategy_mode_schema))

    override_request_strategy_mode_schema = (
        schema["components"]["schemas"]["DeliveryStrategyOverrideRequest"]["properties"]["strategy_mode"]
    )
    assert any(ref.endswith("/StrategyMode") for ref in _enum_refs(override_request_strategy_mode_schema))


@pytest.mark.asyncio
async def test_get_account_credentials_falls_back_to_auto_for_invalid_strategy_mode(
    monkeypatch: pytest.MonkeyPatch,
):
    warnings: list[str] = []

    monkeypatch.setattr(
        account_service.db,
        "get_account_by_email",
        lambda _email: {
            "email": "dirty@example.com",
            "refresh_token": "refresh-token",
            "client_id": "client-id",
            "strategy_mode": "bogus_mode",
        },
    )
    monkeypatch.setattr(
        account_service.logger,
        "warning",
        lambda message: warnings.append(message),
    )

    credentials = await account_service.get_account_credentials("dirty@example.com")

    assert credentials.strategy_mode == "auto"
    assert warnings == [
        "Account dirty@example.com has invalid strategy_mode='bogus_mode'; fallback to auto"
    ]


@pytest.mark.asyncio
async def test_get_all_accounts_tolerates_invalid_strategy_mode(
    monkeypatch: pytest.MonkeyPatch,
):
    warnings: list[str] = []

    monkeypatch.setattr(
        account_service.db,
        "get_all_accounts_db",
        lambda **_kwargs: (
            [
                {
                    "email": "dirty@example.com",
                    "client_id": "client-id",
                    "refresh_token": "refresh-token",
                    "strategy_mode": "bogus_mode",
                }
            ],
            1,
        ),
    )
    monkeypatch.setattr(
        account_service.logger,
        "warning",
        lambda message: warnings.append(message),
    )

    response = await account_service.get_all_accounts(page=1, page_size=10)

    assert response.total_accounts == 1
    assert response.accounts[0].email_id == "dirty@example.com"
    assert response.accounts[0].strategy_mode == "auto"
    assert warnings == [
        "Account dirty@example.com has invalid strategy_mode='bogus_mode'; fallback to auto"
    ]


def test_get_account_health_tolerates_invalid_strategy_mode_from_db(
    monkeypatch: pytest.MonkeyPatch,
):
    warnings: list[str] = []

    monkeypatch.setattr(
        account_service.db,
        "get_account_by_email",
        lambda _email: {
            "email": "dirty@example.com",
            "refresh_token": "refresh-token",
            "client_id": "client-id",
            "strategy_mode": "bogus_mode",
            "capability_snapshot_json": "{}",
            "provider_health_json": "{}",
        },
    )
    monkeypatch.setattr(
        account_service.logger,
        "warning",
        lambda message: warnings.append(message),
    )

    app.dependency_overrides[auth.get_current_user] = _admin_override

    try:
        with TestClient(app) as client:
            response = client.get("/api/v2/accounts/dirty@example.com/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["strategy_mode"] == "auto"
    assert warnings == [
        "Account dirty@example.com has invalid strategy_mode='bogus_mode'; fallback to auto"
    ]


def test_delivery_strategy_explain_matches_runtime_mail_gateway_order():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="graph_api",
        strategy_mode="auto",
        last_provider_used="imap",
        capability_snapshot_json=json.dumps(
            {
                "graph_available": True,
                "graph_read_available": True,
                "recommended_provider": "graph_api",
            }
        ),
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    graph_provider = FakeProvider("graph")
    imap_provider = FakeProvider("imap")
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=lambda *_args: True,
    )
    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_lifecycle_service = service
    app.state.v2_account_loader = load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            explain_response = client.get(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy"
            )
            messages_response = client.get(
                "/api/v2/accounts/mailbox@example.com/messages",
                params={"folder": "inbox", "page": 1, "page_size": 20},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert explain_response.status_code == 200
    assert explain_response.json()["resolved_provider"] == "imap"
    assert explain_response.json()["provider_order"] == ["imap", "graph_api"]
    assert messages_response.status_code == 200
    assert [call[0] for call in imap_provider.calls] == ["list"]
    assert graph_provider.calls == []


def test_delivery_strategy_explain_preview_strategy_mode_matches_messages_route():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="imap_only",
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    graph_provider = FakeProvider("graph")
    imap_provider = FakeProvider("imap")
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=lambda *_args: True,
    )
    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_lifecycle_service = service
    app.state.v2_account_loader = load_credentials
    app.state.v2_mail_gateway = gateway

    try:
        with TestClient(app) as client:
            explain_response = client.get(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy",
                params={"strategy_mode": "graph_preferred", "skip_cache": True},
            )
            messages_response = client.get(
                "/api/v2/accounts/mailbox@example.com/messages",
                params={
                    "folder": "inbox",
                    "page": 1,
                    "page_size": 20,
                    "strategy_mode": "graph_preferred",
                    "skip_cache": True,
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service
        del app.state.v2_account_loader
        del app.state.v2_mail_gateway

    assert explain_response.status_code == 200
    assert explain_response.json()["strategy_mode"] == "graph_preferred"
    assert explain_response.json()["resolved_provider"] == "graph_api"
    assert explain_response.json()["provider_order"] == ["graph_api", "imap"]
    assert messages_response.status_code == 200
    assert [call[0] for call in graph_provider.calls] == ["list"]
    assert imap_provider.calls == []


def test_delivery_strategy_explain_keeps_capability_recommendation_separate_from_override_resolution():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="graph_api",
        strategy_mode="graph_preferred",
        capability_snapshot_json=json.dumps(
            {
                "graph_available": True,
                "graph_read_available": True,
                "recommended_provider": "graph_api",
            }
        ),
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy",
                params={"override_provider": "imap"},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json()["capability"]["recommended_provider"] == "graph_api"
    assert response.json()["resolved_provider"] == "imap"
    assert response.json()["recommended_provider"] == "graph_api"
    assert response.json()["recommended_provider"] != response.json()["resolved_provider"]


def test_delivery_strategy_rejects_invalid_strategy_mode():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy",
                params={"strategy_mode": "bogus_mode"},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 422


def test_delivery_strategy_override_returns_preview_contract_without_persisting():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="auto",
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy/override",
                json={"provider": "graph", "skip_cache": True, "ttl_seconds": 120},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json() == {
        "preview_only": True,
        "persisted": False,
        "effective_for_future_requests": False,
        "message": "override preview only; no state was persisted",
        "requested_override": {
            "provider": "graph",
            "skip_cache": True,
            "ttl_seconds": 120,
        },
        "delivery_strategy_preview": {
            "email": "mailbox@example.com",
            "strategy_mode": "auto",
            "recommended_provider": "imap",
            "resolved_provider": "graph_api",
            "provider_order": ["graph_api"],
            "last_provider_used": None,
            "override_active": True,
            "override_provider": "graph_api",
            "skip_cache": True,
            "capability": {},
        },
    }


def test_delivery_strategy_override_preview_accepts_strategy_mode_input():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="imap_only",
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy/override",
                json={
                    "provider": "auto",
                    "strategy_mode": "graph_preferred",
                    "skip_cache": True,
                    "ttl_seconds": 120,
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json()["requested_override"] == {
        "provider": "auto",
        "strategy_mode": "graph_preferred",
        "skip_cache": True,
        "ttl_seconds": 120,
    }
    assert response.json()["delivery_strategy_preview"]["strategy_mode"] == "graph_preferred"
    assert response.json()["delivery_strategy_preview"]["resolved_provider"] == "graph_api"
    assert response.json()["delivery_strategy_preview"]["provider_order"] == [
        "graph_api",
        "imap",
    ]


def test_delivery_strategy_override_rejects_invalid_strategy_mode():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy/override",
                json={"provider": "auto", "strategy_mode": "bogus_mode", "skip_cache": False},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 422


def test_delivery_strategy_override_requires_admin():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _non_admin_override
    app.dependency_overrides[auth.get_current_admin] = _non_admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy/override",
                json={"provider": "imap", "skip_cache": False},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 403


def test_delivery_strategy_override_rejects_invalid_provider():
    credentials = AccountCredentials(
        email="mailbox@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
    )

    async def load_credentials(_email: str) -> AccountCredentials:
        return credentials

    service = AccountLifecycleService(account_loader=load_credentials)

    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/mailbox@example.com/delivery-strategy/override",
                json={"provider": "smtp", "skip_cache": False},
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 422


def test_capability_detection_requires_admin():
    service = FakeLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _non_admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v2/accounts/mailbox@example.com/capability-detection",
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 403
    assert service.capability_calls == []


class FakeTokenBroker:
    def __init__(self) -> None:
        self.fetch_calls: list[dict] = []

    async def fetch_access_token(self, credentials, *, persist: bool, strategy_mode=None, requested_provider=None):
        self.fetch_calls.append({
            "email": credentials.email,
            "persist": persist,
            "strategy_mode": strategy_mode,
            "requested_provider": requested_provider,
        })
        return object()


class FakeCapabilityResolver:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[dict] = []

    async def detect_capability(self, credentials, *, persist: bool = True, probe_source=None):
        self.calls.append({
            "email": credentials.email,
            "persist": persist,
            "probe_source": probe_source,
        })
        return dict(self.response)


@pytest.mark.asyncio
async def test_probe_account_does_not_prefetch_token_before_capability_probe():
    credentials = AccountCredentials(
        email="probe@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        strategy_mode="auto",
    )
    token_broker = FakeTokenBroker()
    capability_resolver = FakeCapabilityResolver(
        {
            "graph_available": True,
            "graph_read_available": True,
            "graph_write_available": False,
            "graph_send_available": False,
            "imap_available": None,
            "recommended_provider": "graph_api",
            "graph_probe_status": "mail_scope_confirmed",
        }
    )
    service = AccountLifecycleService(
        token_broker=token_broker,
        capability_resolver=capability_resolver,
    )

    result = await service.probe_account(credentials, persist=False)

    assert token_broker.fetch_calls == []
    assert capability_resolver.calls == [
        {
            "email": "probe@example.com",
            "persist": False,
            "probe_source": "api_v2_probe",
        }
    ]
    assert result["token_ok"] is True
    assert result["capability"]["recommended_provider"] == "graph_api"
