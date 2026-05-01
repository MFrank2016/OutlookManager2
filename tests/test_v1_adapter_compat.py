from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import auth
import email_service
import account_service
import cache_service
from main import app
from microsoft_access.account_lifecycle_service import AccountLifecycleService
from microsoft_access.mail_gateway import MailGateway
from models import AccountCredentials, EmailDetailsResponse, EmailItem, EmailListResponse

EXPECTED_V1_SUNSET = "Wed, 31 Dec 2026 23:59:59 GMT"
from routes import account_routes, email_routes, share_routes


class FakeLifecycleService:
    def __init__(self) -> None:
        self.register_calls: list[dict] = []
        self.refresh_calls: list[str] = []
        self.detect_calls: list[str] = []

    async def register_account(self, credentials: AccountCredentials):
        self.register_calls.append(
            {
                "email": credentials.email,
                "refresh_token": credentials.refresh_token,
                "client_id": credentials.client_id,
                "strategy_mode": credentials.strategy_mode,
            }
        )
        return {
            "email_id": credentials.email,
            "message": "Account verified and saved successfully.",
        }

    async def refresh_account_token(self, email_id: str):
        self.refresh_calls.append(email_id)
        return {
            "success": True,
            "email_id": email_id,
            "message": "Token refreshed successfully at 2026-04-30T00:00:00",
        }

    async def detect_api_method(self, email_id: str):
        self.detect_calls.append(email_id)
        return {"email_id": email_id, "api_method": "graph_api"}


class FakeMailGateway:
    def __init__(self) -> None:
        self.list_calls: list[dict] = []
        self.list_with_body_calls: list[dict] = []
        self.detail_calls: list[dict] = []
        self.delete_calls: list[dict] = []
        self.batch_delete_calls: list[dict] = []
        self.send_calls: list[dict] = []

    async def list_messages(self, credentials: AccountCredentials, **kwargs):
        self.list_calls.append({"email": credentials.email, **kwargs})
        return EmailListResponse(
            email_id=credentials.email,
            folder_view=kwargs["folder"],
            page=kwargs["page"],
            page_size=kwargs["page_size"],
            total_pages=1,
            total_emails=2,
            emails=[
                EmailItem(
                    message_id="msg-1",
                    folder="INBOX",
                    subject="Your code 1",
                    from_email="noreply@example.com",
                    date="2026-04-30T00:00:00",
                    sender_initial="N",
                ),
                EmailItem(
                    message_id="msg-2",
                    folder="INBOX",
                    subject="Your code 2",
                    from_email="noreply@example.com",
                    date="2026-04-30T00:01:00",
                    sender_initial="N",
                ),
            ],
        )

    async def list_messages_with_body(self, credentials: AccountCredentials, **kwargs):
        self.list_with_body_calls.append({"email": credentials.email, **kwargs})
        return [
            {
                "message_id": "msg-1",
                "folder": "INBOX",
                "subject": "Your code 1",
                "from_email": "noreply@example.com",
                "date": "2026-04-30T00:00:00",
                "sender_initial": "N",
                "body_plain": "body-msg-1",
                "body_html": "<p>body-msg-1</p>",
                "verification_code": "123456",
            },
            {
                "message_id": "msg-2",
                "folder": "INBOX",
                "subject": "Your code 2",
                "from_email": "noreply@example.com",
                "date": "2026-04-30T00:01:00",
                "sender_initial": "N",
                "body_plain": "body-msg-2",
                "body_html": "<p>body-msg-2</p>",
                "verification_code": "654321",
            },
        ]

    async def get_message_detail(self, credentials: AccountCredentials, message_id: str, **kwargs):
        self.detail_calls.append(
            {
                "email": credentials.email,
                "message_id": message_id,
                **kwargs,
            }
        )
        return EmailDetailsResponse(
            message_id=message_id,
            subject=f"Your code for {message_id}",
            from_email="noreply@example.com",
            to_email=credentials.email,
            date="2026-04-30T00:00:00",
            body_plain=f"body-{message_id}",
            body_html=f"<p>body-{message_id}</p>",
            verification_code="123456",
        )

    async def delete_message(self, credentials: AccountCredentials, message_id: str, **kwargs):
        self.delete_calls.append(
            {
                "email": credentials.email,
                "message_id": message_id,
                **kwargs,
            }
        )
        return True

    async def delete_messages_batch(self, credentials: AccountCredentials, *, folder: str, **kwargs):
        self.batch_delete_calls.append(
            {
                "email": credentials.email,
                "folder": folder,
                **kwargs,
            }
        )
        return {"success_count": 2, "fail_count": 0, "total_count": 2}

    async def send_message(self, credentials: AccountCredentials, **kwargs):
        self.send_calls.append({"email": credentials.email, **kwargs})
        return "sent-msg-1"


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


class _LifecycleTokenBroker:
    def __init__(self) -> None:
        self.fetch_calls: list[dict] = []
        self.refresh_calls: list[dict] = []

    async def fetch_access_token(self, credentials, *, persist: bool, strategy_mode=None, requested_provider=None):
        self.fetch_calls.append(
            {
                "email": credentials.email,
                "persist": persist,
                "strategy_mode": strategy_mode,
                "requested_provider": requested_provider,
            }
        )
        return SimpleNamespace(refresh_token="rotated-refresh-token", provider_hint="graph_api")

    async def refresh_access_token(self, credentials, *, persist: bool, strategy_mode=None, requested_provider=None):
        self.refresh_calls.append(
            {
                "email": credentials.email,
                "persist": persist,
                "strategy_mode": strategy_mode,
                "requested_provider": requested_provider,
            }
        )
        return {
            "success": True,
            "new_refresh_token": "refreshed-token",
            "new_access_token": "access-token",
            "access_token_expires_at": "2026-04-30T01:00:00+00:00",
        }


class _LifecycleTokenBrokerWithoutProviderHint(_LifecycleTokenBroker):
    async def fetch_access_token(
        self,
        credentials,
        *,
        persist: bool,
        strategy_mode=None,
        requested_provider=None,
    ):
        self.fetch_calls.append(
            {
                "email": credentials.email,
                "persist": persist,
                "strategy_mode": strategy_mode,
                "requested_provider": requested_provider,
            }
        )
        return SimpleNamespace(refresh_token="rotated-refresh-token", provider_hint=None)


class _CapabilityResolver:
    async def detect_capability(self, *_args, **_kwargs):
        return {
            "graph_available": True,
            "graph_read_available": True,
            "recommended_provider": "graph_api",
        }


class _StrategyMailGateway:
    def __init__(self) -> None:
        self.resolve_calls: list[dict] = []

    async def resolve_provider_order(self, credentials, *, strategy_mode, override_provider):
        self.resolve_calls.append(
            {
                "email": credentials.email,
                "strategy_mode": strategy_mode,
                "override_provider": override_provider,
            }
        )
        return ["graph_api", "imap"]


class _WriteProvider:
    def __init__(self, name: str) -> None:
        self.name = name
        self.delete_calls: list[dict] = []
        self.batch_delete_calls: list[dict] = []
        self.send_calls: list[dict] = []

    async def delete_message(self, credentials, message_id: str):
        self.delete_calls.append({"email": credentials.email, "message_id": message_id})
        return True

    async def delete_messages_batch(self, credentials, *, folder: str):
        self.batch_delete_calls.append({"email": credentials.email, "folder": folder})
        return {"success_count": 1, "fail_count": 0, "total_count": 1}

    async def send_message(self, credentials, *, to: str, subject: str, body_text=None, body_html=None):
        self.send_calls.append(
            {
                "email": credentials.email,
                "to": to,
                "subject": subject,
                "body_text": body_text,
                "body_html": body_html,
            }
        )
        return f"{self.name}-message-id"


class _NoReadGateway:
    pass


class _RecordingLifecycleAccountDao:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}
        self.create_calls: list[dict] = []
        self.update_calls: list[dict] = []

    def get_by_email(self, email: str):
        return self.records.get(email)

    def create(
        self,
        *,
        email: str,
        refresh_token: str,
        client_id: str,
        tags=None,
        api_method: str = "imap",
        strategy_mode: str = "auto",
        lifecycle_state: str = "new",
        last_provider_used=None,
        capability_snapshot_json=None,
        provider_health_json=None,
    ):
        record = {
            "email": email,
            "refresh_token": refresh_token,
            "client_id": client_id,
            "tags": list(tags or []),
            "api_method": api_method,
            "strategy_mode": strategy_mode,
            "lifecycle_state": lifecycle_state,
            "last_provider_used": last_provider_used,
            "capability_snapshot_json": capability_snapshot_json,
            "provider_health_json": provider_health_json,
        }
        self.records[email] = record
        self.create_calls.append(record.copy())
        return record.copy()

    def update_account(self, email: str, **kwargs):
        record = self.records.setdefault(email, {"email": email})
        record.update(kwargs)
        self.update_calls.append({"email": email, **kwargs})
        return True


@pytest.mark.asyncio
async def test_account_lifecycle_service_exposes_v1_public_write_methods(monkeypatch):
    account_dao = _RecordingLifecycleAccountDao()

    async def load_credentials(email: str) -> AccountCredentials:
        record = account_dao.records.get(email)
        if record is None:
            return AccountCredentials(
                email=email,
                refresh_token="refresh-token",
                client_id="client-id",
                api_method="imap",
                strategy_mode="auto",
            )
        return AccountCredentials(
            email=email,
            refresh_token=record["refresh_token"],
            client_id=record["client_id"],
            api_method=record.get("api_method", "imap"),
            strategy_mode=record.get("strategy_mode", "auto"),
            lifecycle_state=record.get("lifecycle_state", "new"),
            last_provider_used=record.get("last_provider_used"),
            last_refresh_time=record.get("last_refresh_time"),
            next_refresh_time=record.get("next_refresh_time"),
            refresh_status=record.get("refresh_status", "pending"),
            refresh_error=record.get("refresh_error"),
            capability_snapshot_json=record.get("capability_snapshot_json"),
            provider_health_json=record.get("provider_health_json"),
        )

    update_calls: list[dict] = []
    async def fail_save_account_credentials(*_args, **_kwargs):
        raise AssertionError("lifecycle service should persist via its own dao, not account_service")

    monkeypatch.setattr("account_service.save_account_credentials", fail_save_account_credentials)
    monkeypatch.setattr(
        "microsoft_access.account_lifecycle_service.db.update_account",
        lambda email, **kwargs: update_calls.append({"email": email, **kwargs}) or True,
    )

    token_broker = _LifecycleTokenBroker()
    strategy_gateway = _StrategyMailGateway()
    service = AccountLifecycleService(
        token_broker=token_broker,
        capability_resolver=_CapabilityResolver(),
        mail_gateway=strategy_gateway,
        account_loader=load_credentials,
        account_dao=account_dao,
    )

    register_result = await service.register_account(
        AccountCredentials(
            email="writer@example.com",
            refresh_token="refresh-token",
            client_id="client-id",
            strategy_mode="graph_preferred",
        )
    )
    refresh_result = await service.refresh_account_token("writer@example.com")
    detect_result = await service.detect_api_method("writer@example.com")

    assert register_result["email_id"] == "writer@example.com"
    assert refresh_result["success"] is True
    assert detect_result == {"email_id": "writer@example.com", "api_method": "graph_api"}
    assert token_broker.fetch_calls == [
        {
            "email": "writer@example.com",
            "persist": True,
            "strategy_mode": "graph_preferred",
            "requested_provider": None,
        }
    ]
    assert token_broker.refresh_calls == [
        {
            "email": "writer@example.com",
            "persist": True,
            "strategy_mode": "graph_preferred",
            "requested_provider": None,
        }
    ]
    assert strategy_gateway.resolve_calls == []
    assert account_dao.create_calls == [
        {
            "email": "writer@example.com",
            "refresh_token": "rotated-refresh-token",
            "client_id": "client-id",
            "tags": [],
            "api_method": "graph_api",
            "strategy_mode": "graph_preferred",
            "lifecycle_state": "new",
            "last_provider_used": "graph_api",
            "capability_snapshot_json": None,
            "provider_health_json": None,
        }
    ]
    assert account_dao.update_calls[0]["email"] == "writer@example.com"
    assert account_dao.update_calls[0]["refresh_status"] == "success"
    assert account_dao.update_calls[0]["refresh_error"] is None
    assert account_dao.update_calls[0]["last_refresh_time"]
    assert account_dao.update_calls[0]["next_refresh_time"]
    refresh_persist_call = next(
        call for call in account_dao.update_calls if call.get("refresh_token") == "refreshed-token"
    )
    assert refresh_persist_call["email"] == "writer@example.com"
    assert refresh_persist_call["api_method"] == "graph_api"
    assert refresh_persist_call["last_provider_used"] == "graph_api"
    assert refresh_persist_call["refresh_status"] == "success"
    assert update_calls == [{"email": "writer@example.com", "api_method": "graph_api"}]


@pytest.mark.asyncio
async def test_detect_api_method_uses_capability_result_instead_of_stale_api_method(monkeypatch):
    update_calls: list[dict] = []

    async def load_credentials(email: str) -> AccountCredentials:
        return AccountCredentials(
            email=email,
            refresh_token="refresh-token",
            client_id="client-id",
            api_method="imap",
            strategy_mode="auto",
        )

    class GraphCapableResolver:
        async def detect_capability(self, *_args, **_kwargs):
            return {
                "graph_available": True,
                "graph_read_available": True,
                "recommended_provider": "graph_api",
            }

    class ResolveMustNotRunGateway:
        async def resolve_provider_order(self, *_args, **_kwargs):
            raise AssertionError("detect_api_method should not call resolve_provider_order")

    class RecordingAccountDao:
        def update_account(self, email: str, **kwargs):
            update_calls.append({"email": email, **kwargs})
            return True

    monkeypatch.setattr(
        "microsoft_access.account_lifecycle_service.db.update_account",
        lambda email, **kwargs: update_calls.append({"email": email, **kwargs}) or True,
    )

    service = AccountLifecycleService(
        capability_resolver=GraphCapableResolver(),
        mail_gateway=ResolveMustNotRunGateway(),
        account_loader=load_credentials,
        account_dao=RecordingAccountDao(),
    )

    result = await service.detect_api_method("writer@example.com")

    assert result == {"email_id": "writer@example.com", "api_method": "graph_api"}
    assert update_calls == [
        {"email": "writer@example.com", "lifecycle_state": "probed"},
        {"email": "writer@example.com", "api_method": "graph_api"},
    ]


@pytest.mark.asyncio
async def test_register_account_preserves_existing_metadata_when_request_does_not_explicitly_set_it():
    account_dao = _RecordingLifecycleAccountDao()
    account_dao.records["writer@example.com"] = {
        "email": "writer@example.com",
        "refresh_token": "old-refresh-token",
        "client_id": "old-client-id",
        "tags": ["vip", "keep-me"],
        "api_method": "graph_api",
        "strategy_mode": "graph_preferred",
        "lifecycle_state": "healthy",
        "last_provider_used": "graph_api",
        "capability_snapshot_json": '{"recommended_provider":"graph_api"}',
        "provider_health_json": '{"last_error_message":"keep"}',
    }

    service = AccountLifecycleService(
        token_broker=_LifecycleTokenBrokerWithoutProviderHint(),
        capability_resolver=_CapabilityResolver(),
        mail_gateway=_StrategyMailGateway(),
        account_dao=account_dao,
    )

    await service.register_account(
        AccountCredentials(
            email="writer@example.com",
            refresh_token="new-refresh-token",
            client_id="new-client-id",
            strategy_mode="auto",
        )
    )

    record = account_dao.records["writer@example.com"]
    assert record["refresh_token"] == "rotated-refresh-token"
    assert record["client_id"] == "new-client-id"
    assert record["strategy_mode"] == "auto"
    assert record["tags"] == ["vip", "keep-me"]
    assert record["api_method"] == "graph_api"
    assert record["lifecycle_state"] == "healthy"
    assert record["last_provider_used"] == "graph_api"
    assert record["capability_snapshot_json"] == '{"recommended_provider":"graph_api"}'
    assert record["provider_health_json"] == '{"last_error_message":"keep"}'

    persisted_payload = account_dao.update_calls[-1]
    assert persisted_payload["email"] == "writer@example.com"
    assert "tags" not in persisted_payload
    assert "api_method" not in persisted_payload
    assert "lifecycle_state" not in persisted_payload
    assert "capability_snapshot_json" not in persisted_payload
    assert "provider_health_json" not in persisted_payload
    assert persisted_payload["refresh_status"] == "success"
    assert persisted_payload["refresh_error"] is None
    assert persisted_payload["last_refresh_time"]
    assert persisted_payload["next_refresh_time"]


@pytest.mark.asyncio
async def test_refresh_and_detect_tolerate_invalid_historical_strategy_mode(monkeypatch):
    warnings: list[str] = []
    account_dao = _RecordingLifecycleAccountDao()
    account_dao.records["dirty@example.com"] = {
        "email": "dirty@example.com",
        "refresh_token": "old-refresh-token",
        "client_id": "client-id",
        "tags": ["keep-me"],
        "api_method": "imap",
        "strategy_mode": "bogus_mode",
        "lifecycle_state": "healthy",
        "capability_snapshot_json": '{"recommended_provider":"graph_api"}',
        "provider_health_json": '{"last_error_message":"keep"}',
    }
    detect_updates: list[dict] = []

    monkeypatch.setattr(
        "microsoft_access.account_lifecycle_service.logger.warning",
        lambda message: warnings.append(message),
    )

    service = AccountLifecycleService(
        token_broker=_LifecycleTokenBroker(),
        capability_resolver=_CapabilityResolver(),
        mail_gateway=_StrategyMailGateway(),
        account_dao=account_dao,
        db_module=SimpleNamespace(
            update_account=lambda email, **kwargs: detect_updates.append(
                {"email": email, **kwargs}
            )
            or True
        ),
    )

    detect_result = await service.detect_api_method("dirty@example.com")
    refresh_result = await service.refresh_account_token("dirty@example.com")

    assert detect_result == {"email_id": "dirty@example.com", "api_method": "graph_api"}
    assert refresh_result["success"] is True
    assert warnings == [
        "Account dirty@example.com has invalid strategy_mode='bogus_mode'; fallback to auto",
        "Account dirty@example.com has invalid strategy_mode='bogus_mode'; fallback to auto",
    ]
    assert detect_updates == [{"email": "dirty@example.com", "api_method": "graph_api"}]
    persisted_refresh = next(
        call for call in account_dao.update_calls if call.get("refresh_token") == "refreshed-token"
    )
    assert persisted_refresh["strategy_mode"] == "auto"
    assert persisted_refresh["tags"] == ["keep-me"]


@pytest.mark.asyncio
async def test_mail_gateway_exposes_v1_public_write_methods():
    graph_provider = _WriteProvider("graph")
    imap_provider = _WriteProvider("imap")
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=lambda *_args: True,
    )
    credentials = AccountCredentials(
        email="writer@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="graph_api",
        strategy_mode="auto",
    )

    delete_result = await gateway.delete_message(credentials, "msg-1")
    batch_delete_result = await gateway.delete_messages_batch(credentials, folder="inbox")
    send_result = await gateway.send_message(
        credentials,
        to="target@example.com",
        subject="Hello",
        body_text="plain body",
    )

    assert delete_result is True
    assert batch_delete_result == {"success_count": 1, "fail_count": 0, "total_count": 1}
    assert send_result == "graph-message-id"
    assert graph_provider.delete_calls == [{"email": "writer@example.com", "message_id": "msg-1"}]
    assert graph_provider.batch_delete_calls == [{"email": "writer@example.com", "folder": "inbox"}]
    assert graph_provider.send_calls == [
        {
            "email": "writer@example.com",
            "to": "target@example.com",
            "subject": "Hello",
            "body_text": "plain body",
            "body_html": None,
        }
    ]
    assert imap_provider.delete_calls == []


@pytest.mark.asyncio
async def test_list_messages_via_gateway_does_not_fallback_to_legacy_email_service(monkeypatch):
    called = {"legacy": False}

    async def fail_legacy_list_messages(*_args, **_kwargs):
        called["legacy"] = True
        raise AssertionError("legacy email_service.list_emails should not be used")

    monkeypatch.setattr(email_service, "list_emails", fail_legacy_list_messages)

    credentials = AccountCredentials(
        email="reader@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="auto",
    )

    with pytest.raises(AttributeError):
        await account_service.list_messages_via_gateway(
            _NoReadGateway(),
            credentials,
            folder="inbox",
            page=1,
            page_size=20,
        )

    assert called["legacy"] is False


@pytest.mark.asyncio
async def test_get_message_detail_via_gateway_does_not_fallback_to_legacy_email_service(monkeypatch):
    called = {"legacy": False}

    async def fail_legacy_get_email_details(*_args, **_kwargs):
        called["legacy"] = True
        raise AssertionError("legacy email_service.get_email_details should not be used")

    monkeypatch.setattr(email_service, "get_email_details", fail_legacy_get_email_details)

    credentials = AccountCredentials(
        email="reader@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="auto",
    )

    with pytest.raises(AttributeError):
        await account_service.get_message_detail_via_gateway(
            _NoReadGateway(),
            credentials,
            "msg-1",
        )

    assert called["legacy"] is False


def test_v1_accounts_post_uses_lifecycle_register(monkeypatch):
    service = FakeLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service
    monkeypatch.setattr(
        account_routes,
        "get_access_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy token path should not be used")),
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/accounts",
                json={
                    "email": "mailbox@example.com",
                    "refresh_token": "refresh-token",
                    "client_id": "client-id",
                    "strategy_mode": "graph_preferred",
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert response.status_code == 200
    assert response.json() == {
        "email_id": "mailbox@example.com",
        "message": "Account verified and saved successfully.",
    }
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == EXPECTED_V1_SUNSET
    assert service.register_calls == [
        {
            "email": "mailbox@example.com",
            "refresh_token": "refresh-token",
            "client_id": "client-id",
            "strategy_mode": "graph_preferred",
        }
    ]


def test_v1_emails_get_uses_mail_gateway(monkeypatch):
    gateway = FakeMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_mail_gateway = gateway
    monkeypatch.setattr(email_routes, "get_account_credentials", _load_credentials)
    monkeypatch.setattr(
        email_routes,
        "list_emails",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy email_service.list_emails should not be used")),
    )

    try:
        with TestClient(app) as client:
            response = client.get(
                "/emails/mailbox@example.com",
                params={
                    "folder": "junk",
                    "page": 2,
                    "page_size": 50,
                    "refresh": "true",
                    "sender_search": "noreply",
                    "subject_search": "code",
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_mail_gateway

    assert response.status_code == 200
    assert response.json()["email_id"] == "mailbox@example.com"
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == EXPECTED_V1_SUNSET
    assert gateway.list_calls == [
        {
            "email": "mailbox@example.com",
            "folder": "junk",
            "page": 2,
            "page_size": 50,
            "strategy_mode": "auto",
            "override_provider": None,
            "skip_cache": True,
            "sender_search": "noreply",
            "subject_search": "code",
            "sort_by": "date",
            "sort_order": "desc",
            "start_time": None,
            "end_time": None,
        }
    ]


def test_share_routes_do_not_fallback_to_legacy_email_service_read_paths(monkeypatch):
    cache_service.clear_share_email_cache("test-token")
    app.state.v2_mail_gateway = _NoReadGateway()
    monkeypatch.setattr(share_routes, "get_account_credentials", _load_credentials)
    app.dependency_overrides[share_routes.get_valid_share_token] = lambda: {
        "email_account_id": "mailbox@example.com",
        "start_time": "2026-04-30T00:00:00",
        "end_time": "2026-04-30T23:59:59",
        "subject_keyword": "code",
        "sender_keyword": "noreply",
        "max_emails": 2,
        "is_active": True,
    }

    async def fail_legacy_list_messages(*_args, **_kwargs):
        raise AssertionError("legacy email_service.list_emails should not be used")

    async def fail_legacy_get_email_details(*_args, **_kwargs):
        raise AssertionError("legacy email_service.get_email_details should not be used")

    monkeypatch.setattr(email_service, "list_emails", fail_legacy_list_messages)
    monkeypatch.setattr(email_service, "get_email_details", fail_legacy_get_email_details)
    monkeypatch.setattr(share_routes.db, "get_cached_email_detail", lambda *_args, **_kwargs: None)

    try:
        with TestClient(app) as client:
            list_response = client.get("/share/test-token/emails")
            detail_response = client.get("/share/test-token/emails/msg-1")
    finally:
        app.dependency_overrides.clear()
        cache_service.clear_share_email_cache("test-token")
        del app.state.v2_mail_gateway

    assert list_response.status_code == 200
    assert list_response.json()["emails"] == []
    assert detail_response.status_code == 404


def test_v1_account_refresh_and_detect_use_lifecycle_public_api(monkeypatch):
    service = FakeLifecycleService()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.dependency_overrides[auth.get_current_admin] = _admin_override
    app.state.v2_account_lifecycle_service = service
    monkeypatch.setattr(
        account_routes,
        "refresh_account_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy oauth refresh path should not be used")),
    )

    try:
        with TestClient(app) as client:
            refresh_response = client.post("/accounts/mailbox@example.com/refresh-token")
            detect_response = client.post("/accounts/mailbox@example.com/detect-api-method")
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_account_lifecycle_service

    assert refresh_response.status_code == 200
    assert refresh_response.json() == {
        "email_id": "mailbox@example.com",
        "message": "Token refreshed successfully at 2026-04-30T00:00:00",
    }
    assert refresh_response.headers["Deprecation"] == "true"
    assert refresh_response.headers["Sunset"] == EXPECTED_V1_SUNSET
    assert detect_response.status_code == 200
    assert detect_response.json() == {
        "email_id": "mailbox@example.com",
        "message": "API method detected and updated to: graph_api",
    }
    assert detect_response.headers["Deprecation"] == "true"
    assert detect_response.headers["Sunset"] == EXPECTED_V1_SUNSET
    assert service.refresh_calls == ["mailbox@example.com"]
    assert service.detect_calls == ["mailbox@example.com"]


def test_v1_email_write_routes_use_mail_gateway_public_api(monkeypatch):
    gateway = FakeMailGateway()
    app.dependency_overrides[auth.get_current_user] = _admin_override
    app.state.v2_mail_gateway = gateway
    monkeypatch.setattr(email_routes, "get_account_credentials", _load_credentials)
    monkeypatch.setattr(
        email_service,
        "delete_email",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy email_service.delete_email should not be used")),
    )
    monkeypatch.setattr(
        email_service,
        "delete_emails_batch",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy email_service.delete_emails_batch should not be used")),
    )
    monkeypatch.setattr(
        email_service,
        "send_email",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy email_service.send_email should not be used")),
    )

    try:
        with TestClient(app) as client:
            delete_response = client.delete("/emails/mailbox@example.com/msg-7")
            batch_delete_response = client.delete(
                "/emails/mailbox@example.com/batch",
                params={"folder": "junk"},
            )
            send_response = client.post(
                "/emails/mailbox@example.com/send",
                json={
                    "to": "target@example.com",
                    "subject": "hello",
                    "body_text": "plain body",
                },
            )
    finally:
        app.dependency_overrides.clear()
        del app.state.v2_mail_gateway

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "success": True,
        "message": "Email deleted successfully",
        "message_id": "msg-7",
    }
    assert delete_response.headers["Deprecation"] == "true"
    assert delete_response.headers["Sunset"] == EXPECTED_V1_SUNSET
    assert batch_delete_response.status_code == 200
    assert batch_delete_response.json() == {
        "success": True,
        "message": "Successfully deleted 2 emails, 0 failed",
        "success_count": 2,
        "fail_count": 0,
        "total_count": 2,
    }
    assert batch_delete_response.headers["Deprecation"] == "true"
    assert batch_delete_response.headers["Sunset"] == EXPECTED_V1_SUNSET
    assert send_response.status_code == 200
    assert send_response.json() == {
        "success": True,
        "message": "Email sent successfully",
        "message_id": "sent-msg-1",
    }
    assert send_response.headers["Deprecation"] == "true"
    assert send_response.headers["Sunset"] == EXPECTED_V1_SUNSET
    assert gateway.delete_calls == [
        {
            "email": "mailbox@example.com",
            "message_id": "msg-7",
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
            "body_text": "plain body",
            "body_html": None,
            "strategy_mode": "auto",
            "override_provider": None,
        }
    ]


def test_share_route_uses_mail_gateway_detail_path(monkeypatch):
    cache_service.clear_share_email_cache("test-token")
    gateway = FakeMailGateway()
    gateway.list_messages_with_body = None
    app.state.v2_mail_gateway = gateway
    monkeypatch.setattr(share_routes, "get_account_credentials", _load_credentials)
    app.dependency_overrides[share_routes.get_valid_share_token] = lambda: {
        "email_account_id": "mailbox@example.com",
        "start_time": "2026-04-30T00:00:00",
        "end_time": "2026-04-30T23:59:59",
        "subject_keyword": "code",
        "sender_keyword": "noreply",
        "max_emails": 2,
        "is_active": True,
    }
    try:
        with TestClient(app) as client:
            response = client.get("/share/test-token/emails")
    finally:
        app.dependency_overrides.clear()
        cache_service.clear_share_email_cache("test-token")
        del app.state.v2_mail_gateway

    assert response.status_code == 200
    payload = response.json()
    assert payload["email_id"] == "mailbox@example.com"
    assert [email["body_plain"] for email in payload["emails"]] == [
        "body-msg-1",
        "body-msg-2",
    ]
    assert gateway.list_calls == [
        {
            "email": "mailbox@example.com",
            "folder": "all",
            "page": 1,
            "page_size": 2,
            "strategy_mode": "auto",
            "override_provider": None,
            "skip_cache": False,
            "sender_search": "noreply",
            "subject_search": "code",
            "sort_by": "date",
            "sort_order": "desc",
            "start_time": "2026-04-30T00:00:00",
            "end_time": "2026-04-30T23:59:59",
        }
    ]
    assert gateway.detail_calls == [
        {
            "email": "mailbox@example.com",
            "message_id": "msg-1",
            "strategy_mode": "auto",
            "override_provider": None,
            "skip_cache": False,
        },
        {
            "email": "mailbox@example.com",
            "message_id": "msg-2",
            "strategy_mode": "auto",
            "override_provider": None,
            "skip_cache": False,
        },
    ]


def test_share_route_prefers_bulk_body_read_path_over_n_plus_one_detail(monkeypatch):
    cache_service.clear_share_email_cache("test-token")
    gateway = FakeMailGateway()
    app.state.v2_mail_gateway = gateway
    monkeypatch.setattr(share_routes, "get_account_credentials", _load_credentials)
    app.dependency_overrides[share_routes.get_valid_share_token] = lambda: {
        "email_account_id": "mailbox@example.com",
        "start_time": "2026-04-30T00:00:00",
        "end_time": "2026-04-30T23:59:59",
        "subject_keyword": "code",
        "sender_keyword": "noreply",
        "max_emails": 2,
        "is_active": True,
    }
    try:
        with TestClient(app) as client:
            response = client.get("/share/test-token/emails")
    finally:
        app.dependency_overrides.clear()
        cache_service.clear_share_email_cache("test-token")
        del app.state.v2_mail_gateway

    assert response.status_code == 200
    payload = response.json()
    assert [email["body_plain"] for email in payload["emails"]] == [
        "body-msg-1",
        "body-msg-2",
    ]
    assert gateway.list_with_body_calls == [
        {
            "email": "mailbox@example.com",
            "folder": "all",
            "page": 1,
            "page_size": 2,
            "strategy_mode": "auto",
            "override_provider": None,
            "skip_cache": False,
            "sender_search": "noreply",
            "subject_search": "code",
            "sort_by": "date",
            "sort_order": "desc",
            "start_time": "2026-04-30T00:00:00",
            "end_time": "2026-04-30T23:59:59",
        }
    ]
    assert gateway.detail_calls == []
