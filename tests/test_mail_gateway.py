from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import HTTPException

import cache_service
import database as db
from microsoft_access.providers import graph_provider, imap_provider
from models import AccountCredentials, EmailDetailsResponse, EmailItem, EmailListResponse
from microsoft_access.mail_gateway import MailGateway


def noop_persist_provider_hint(_email: str, _provider_name: str) -> bool:
    return True


@dataclass
class FakeProvider:
    name: str
    list_response: EmailListResponse | None = None
    detail_response: EmailDetailsResponse | None = None
    list_error: Exception | None = None
    detail_error: Exception | None = None
    calls: list[tuple[str, dict]] | None = None

    def __post_init__(self) -> None:
        if self.calls is None:
            self.calls = []

    async def list_messages(self, credentials: AccountCredentials, **kwargs) -> EmailListResponse:
        self.calls.append(("list", {"email": credentials.email, **kwargs}))
        if self.list_error is not None:
            raise self.list_error
        assert self.list_response is not None
        return self.list_response

    async def get_message_detail(
        self,
        credentials: AccountCredentials,
        message_id: str,
        **kwargs,
    ) -> EmailDetailsResponse:
        self.calls.append(
            (
                "detail",
                {"email": credentials.email, "message_id": message_id, **kwargs},
            )
        )
        if self.detail_error is not None:
            raise self.detail_error
        assert self.detail_response is not None
        return self.detail_response


@pytest.fixture
def credentials() -> AccountCredentials:
    return AccountCredentials(
        email="mail-gateway@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="auto",
    )


@pytest.fixture
def email_list_response(credentials: AccountCredentials) -> EmailListResponse:
    return EmailListResponse(
        email_id=credentials.email,
        folder_view="inbox",
        page=1,
        page_size=20,
        total_pages=1,
        total_emails=1,
        emails=[
            EmailItem(
                message_id="INBOX-1",
                folder="INBOX",
                subject="Your security code",
                from_email="noreply@example.com",
                date="2026-04-30T00:00:00",
                sender_initial="N",
            )
        ],
    )


@pytest.fixture
def email_detail_response() -> EmailDetailsResponse:
    return EmailDetailsResponse(
        message_id="INBOX-1",
        subject="Your security code",
        from_email="noreply@example.com",
        to_email="mail-gateway@example.com",
        date="2026-04-30T00:00:00",
        body_plain="Your code is 123456",
        verification_code="123456",
    )


@pytest.mark.asyncio
async def test_mail_gateway_uses_override_provider_first(credentials, email_list_response):
    graph_provider = FakeProvider(name="graph", list_response=email_list_response)
    imap_provider = FakeProvider(name="imap", list_response=email_list_response)
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    response = await gateway.list_messages(
        credentials,
        folder="inbox",
        page=1,
        page_size=20,
        override_provider="imap",
    )

    assert response is email_list_response
    assert [call[0] for call in imap_provider.calls] == ["list"]
    assert graph_provider.calls == []
    assert credentials.last_provider_used == "imap"


@pytest.mark.asyncio
async def test_mail_gateway_auto_mode_falls_back_from_graph_to_imap(
    credentials,
    email_list_response,
):
    graph_provider = FakeProvider(
        name="graph",
        list_error=HTTPException(status_code=503, detail="graph unavailable"),
    )
    imap_provider = FakeProvider(name="imap", list_response=email_list_response)

    async def fake_graph_probe(_credentials: AccountCredentials) -> dict:
        return {
            "available": True,
            "graph_available": True,
            "graph_read_available": True,
            "availability_status": "mail_scope_confirmed",
        }

    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        graph_probe=fake_graph_probe,
        persist_provider_hint=noop_persist_provider_hint,
    )
    credentials.api_method = ""
    credentials.last_provider_used = None

    response = await gateway.list_messages(
        credentials,
        folder="inbox",
        page=1,
        page_size=20,
        strategy_mode="auto",
    )

    assert response is email_list_response
    assert [provider_call[0] for provider_call in graph_provider.calls] == ["list"]
    assert [provider_call[0] for provider_call in imap_provider.calls] == ["list"]
    assert credentials.last_provider_used == "imap"


@pytest.mark.asyncio
async def test_mail_gateway_list_returns_email_list_response_shape(
    credentials,
    email_list_response,
):
    graph_provider = FakeProvider(name="graph", list_response=email_list_response)
    imap_provider = FakeProvider(name="imap", list_response=email_list_response)
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    response = await gateway.list_messages(
        credentials,
        folder="inbox",
        page=1,
        page_size=20,
        override_provider="graph",
        skip_cache=True,
        subject_search="security",
        sort_by="date",
        sort_order="desc",
    )

    assert isinstance(response, EmailListResponse)
    assert response.email_id == credentials.email
    assert response.folder_view == "inbox"
    assert response.total_emails == 1
    assert response.emails[0].message_id == "INBOX-1"
    assert graph_provider.calls[0][1]["skip_cache"] is True
    assert graph_provider.calls[0][1]["subject_search"] == "security"


@pytest.mark.asyncio
async def test_mail_gateway_detail_returns_email_details_response_shape(
    credentials,
    email_detail_response,
):
    graph_provider = FakeProvider(name="graph", detail_response=email_detail_response)
    imap_provider = FakeProvider(name="imap", detail_response=email_detail_response)
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    response = await gateway.get_message_detail(
        credentials,
        message_id="INBOX-1",
        override_provider="graph",
    )

    assert isinstance(response, EmailDetailsResponse)
    assert response.message_id == "INBOX-1"
    assert response.verification_code == "123456"
    assert graph_provider.calls[0][0] == "detail"


@pytest.mark.asyncio
async def test_mail_gateway_prefers_provider_bulk_body_path(credentials):
    class BulkGraphProvider(FakeProvider):
        async def list_messages_with_body(self, credentials: AccountCredentials, **kwargs):
            self.calls.append(("list_with_body", {"email": credentials.email, **kwargs}))
            return [
                {
                    "message_id": "INBOX-1",
                    "subject": "Your security code",
                    "body_plain": "Your code is 123456",
                }
            ]

    graph_provider = BulkGraphProvider(name="graph")
    imap_provider = FakeProvider(name="imap")
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    response = await gateway.list_messages_with_body(
        credentials.model_copy(update={"api_method": "graph_api", "last_provider_used": "graph_api"}),
        folder="all",
        page=1,
        page_size=5,
        override_provider="graph",
    )

    assert response == [
        {
            "message_id": "INBOX-1",
            "subject": "Your security code",
            "body_plain": "Your code is 123456",
        }
    ]
    assert graph_provider.calls == [
        (
            "list_with_body",
            {
                "email": "mail-gateway@example.com",
                "folder": "all",
                "page": 1,
                "page_size": 5,
                "skip_cache": False,
                "sender_search": None,
                "subject_search": None,
                "sort_by": "date",
                "sort_order": "desc",
                "start_time": None,
                "end_time": None,
            },
        )
    ]
    assert imap_provider.calls == []


@pytest.mark.asyncio
async def test_mail_gateway_list_with_body_falls_back_from_graph_bulk_503_to_imap(
    credentials,
):
    class Bulk503GraphProvider(FakeProvider):
        async def list_messages_with_body(self, credentials: AccountCredentials, **kwargs):
            self.calls.append(("list_with_body", {"email": credentials.email, **kwargs}))
            raise HTTPException(status_code=503, detail="graph bulk unavailable")

    class BulkImapProvider(FakeProvider):
        async def list_messages_with_body(self, credentials: AccountCredentials, **kwargs):
            self.calls.append(("list_with_body", {"email": credentials.email, **kwargs}))
            return [
                {
                    "message_id": "INBOX-1",
                    "subject": "Fallback IMAP body",
                    "body_plain": "Your code is 654321",
                }
            ]

    graph_provider = Bulk503GraphProvider(name="graph")
    imap_provider = BulkImapProvider(name="imap")
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )
    request_credentials = credentials.model_copy(
        update={"api_method": "graph_api", "last_provider_used": None}
    )

    response = await gateway.list_messages_with_body(
        request_credentials,
        folder="all",
        page=1,
        page_size=5,
        strategy_mode="graph_preferred",
    )

    assert response == [
        {
            "message_id": "INBOX-1",
            "subject": "Fallback IMAP body",
            "body_plain": "Your code is 654321",
        }
    ]
    assert [call[0] for call in graph_provider.calls] == ["list_with_body"]
    assert [call[0] for call in imap_provider.calls] == ["list_with_body"]
    assert request_credentials.last_provider_used == "imap"


@pytest.mark.asyncio
async def test_mail_gateway_detail_keeps_graph_503_for_graph_style_message_id(
    credentials,
):
    graph_fake_provider = FakeProvider(
        name="graph",
        detail_error=HTTPException(status_code=503, detail="graph detail unavailable"),
    )
    gateway = MailGateway(
        graph_provider=graph_fake_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    with pytest.raises(HTTPException) as exc_info:
        await gateway.get_message_detail(
            credentials.model_copy(update={"api_method": "graph_api"}),
            message_id="AAMkAGI2TgraphOnlyId",
            strategy_mode="graph_preferred",
            skip_cache=True,
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "graph detail unavailable"


@pytest.mark.asyncio
async def test_mail_gateway_auto_mode_with_imap_api_method_does_not_probe_graph(
    credentials,
    email_list_response,
):
    probe_calls: list[str] = []
    graph_provider = FakeProvider(name="graph", list_response=email_list_response)
    imap_provider = FakeProvider(name="imap", list_response=email_list_response)

    async def fake_graph_probe(_credentials: AccountCredentials) -> dict:
        probe_calls.append("probe")
        return {
            "available": True,
            "graph_available": True,
            "graph_read_available": True,
            "availability_status": "mail_scope_confirmed",
        }

    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        graph_probe=fake_graph_probe,
        persist_provider_hint=noop_persist_provider_hint,
    )

    response = await gateway.list_messages(
        credentials,
        folder="inbox",
        page=1,
        page_size=20,
        strategy_mode="auto",
    )

    assert response is email_list_response
    assert probe_calls == []
    assert graph_provider.calls == []
    assert [call[0] for call in imap_provider.calls] == ["list"]


@pytest.mark.asyncio
async def test_mail_gateway_auto_mode_prefers_last_provider_used_for_list_and_detail(
    credentials,
    email_list_response,
    email_detail_response,
):
    probe_calls: list[str] = []
    graph_provider = FakeProvider(
        name="graph",
        list_response=email_list_response,
        detail_response=email_detail_response,
    )
    imap_provider = FakeProvider(
        name="imap",
        list_response=email_list_response,
        detail_response=email_detail_response,
    )
    credentials.api_method = "graph_api"
    credentials.last_provider_used = "imap"

    async def fake_graph_probe(_credentials: AccountCredentials) -> dict:
        probe_calls.append("probe")
        return {
            "available": True,
            "graph_available": True,
            "graph_read_available": True,
            "availability_status": "mail_scope_confirmed",
        }

    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        graph_probe=fake_graph_probe,
        persist_provider_hint=noop_persist_provider_hint,
    )

    list_response = await gateway.list_messages(
        credentials,
        folder="inbox",
        page=1,
        page_size=20,
        strategy_mode="auto",
    )
    detail_response = await gateway.get_message_detail(
        credentials,
        message_id="INBOX-1",
        strategy_mode="auto",
    )

    assert list_response is email_list_response
    assert detail_response is email_detail_response
    assert probe_calls == []
    assert graph_provider.calls == []
    assert [call[0] for call in imap_provider.calls] == ["list", "detail"]


@pytest.mark.asyncio
async def test_mail_gateway_does_not_fallback_on_nonrecoverable_provider_error(
    credentials,
    email_list_response,
):
    graph_provider = FakeProvider(
        name="graph",
        list_error=ValueError("coding error"),
    )
    imap_provider = FakeProvider(name="imap", list_response=email_list_response)
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    with pytest.raises(ValueError, match="coding error"):
        await gateway.list_messages(
            credentials.model_copy(update={"api_method": "graph_api"}),
            folder="inbox",
            page=1,
            page_size=20,
            strategy_mode="graph_preferred",
        )

    assert [call[0] for call in graph_provider.calls] == ["list"]
    assert imap_provider.calls == []


@pytest.mark.asyncio
async def test_mail_gateway_persists_fallback_provider_for_next_request_detail(
    credentials,
    email_list_response,
    email_detail_response,
):
    persisted: dict[str, str | None] = {"last_provider_used": None}
    graph_provider = FakeProvider(
        name="graph",
        list_error=HTTPException(status_code=503, detail="graph unavailable"),
        detail_response=email_detail_response,
    )
    imap_provider = FakeProvider(
        name="imap",
        list_response=email_list_response,
        detail_response=email_detail_response,
    )

    async def fake_graph_probe(_credentials: AccountCredentials) -> dict:
        return {
            "available": True,
            "graph_available": True,
            "graph_read_available": True,
            "availability_status": "mail_scope_confirmed",
        }

    def persist_provider_hint(email: str, provider_name: str) -> bool:
        assert email == credentials.email
        persisted["last_provider_used"] = provider_name
        return True

    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        graph_probe=fake_graph_probe,
        persist_provider_hint=persist_provider_hint,
    )
    credentials.api_method = ""
    credentials.last_provider_used = None

    list_response = await gateway.list_messages(
        credentials,
        folder="inbox",
        page=1,
        page_size=20,
        strategy_mode="auto",
    )

    next_request_credentials = AccountCredentials(
        email=credentials.email,
        refresh_token=credentials.refresh_token,
        client_id=credentials.client_id,
        api_method="",
        strategy_mode="auto",
        last_provider_used=persisted["last_provider_used"],
    )
    detail_gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        graph_probe=fake_graph_probe,
        persist_provider_hint=persist_provider_hint,
    )
    detail_response = await detail_gateway.get_message_detail(
        next_request_credentials,
        message_id=list_response.emails[0].message_id,
        strategy_mode="auto",
    )

    assert persisted["last_provider_used"] == "imap"
    assert detail_response is email_detail_response
    assert [call[0] for call in graph_provider.calls] == ["list"]
    assert [call[0] for call in imap_provider.calls] == ["list", "detail"]


@pytest.mark.asyncio
async def test_mail_gateway_does_not_fallback_on_runtime_error(
    credentials,
    email_list_response,
):
    graph_provider = FakeProvider(
        name="graph",
        list_error=RuntimeError("unexpected implementation bug"),
    )
    imap_provider = FakeProvider(name="imap", list_response=email_list_response)
    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    with pytest.raises(RuntimeError, match="unexpected implementation bug"):
        await gateway.list_messages(
            credentials.model_copy(update={"api_method": "graph_api"}),
            folder="inbox",
            page=1,
            page_size=20,
            strategy_mode="graph_preferred",
        )

    assert [call[0] for call in graph_provider.calls] == ["list"]
    assert imap_provider.calls == []


@pytest.mark.asyncio
async def test_graph_cached_list_does_not_leak_into_imap_route(monkeypatch: pytest.MonkeyPatch):
    email = "provider-cache-isolation@example.com"
    cache_service.email_list_cache.clear()
    cache_service.email_detail_cache.clear()
    db.clear_email_cache_db(email)

    graph_credentials = AccountCredentials(
        email=email,
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="",
        strategy_mode="auto",
    )

    graph_item = EmailItem(
        message_id="graph-message-id",
        folder="inbox",
        subject="Graph security code",
        from_email="graph@example.com",
        date="2026-04-30T00:00:00",
        sender_initial="G",
    )

    async def fake_list_emails_graph2(*_args, **_kwargs):
        return [graph_item], 1

    async def fake_get_cached_access_token(_credentials: AccountCredentials) -> str:
        return "token"

    class FakeImapClient:
        state = "SELECTED"

        def select(self, *_args, **_kwargs):
            return "OK", [b""]

        def search(self, *_args, **_kwargs):
            return "OK", [b"1"]

        def fetch(self, message_set, _query):
            if isinstance(message_set, bytes) and b"," in message_set:
                response_prefix = message_set.split(b",", 1)[0]
            elif isinstance(message_set, bytes):
                response_prefix = message_set
            else:
                response_prefix = str(message_set).encode()
            header_bytes = (
                b"Subject: IMAP security code\r\n"
                b"From: imap@example.com\r\n"
                b"Date: Thu, 30 Apr 2026 00:00:00 +0000\r\n"
                b"Message-ID: <imap-1@example.com>\r\n\r\n"
            )
            return "OK", [
                (
                    response_prefix + b" (BODY[HEADER.FIELDS (SUBJECT DATE FROM MESSAGE-ID)] {128}",
                    header_bytes,
                ),
                b")",
            ]

    class FakeImapPool:
        def get_connection(self, _email: str, _access_token: str):
            return FakeImapClient()

        def return_connection(self, _email: str, _imap_client) -> None:
            return None

    monkeypatch.setattr("graph_api_service.list_emails_graph2", fake_list_emails_graph2)
    monkeypatch.setattr("email_service.get_cached_access_token", fake_get_cached_access_token)
    monkeypatch.setattr("email_service.imap_pool", FakeImapPool())
    monkeypatch.setattr(
        "email_service.detect_verification_code_with_rules",
        lambda **_kwargs: {},
    )

    graph_response = await graph_provider.list_messages(
        graph_credentials,
        folder="inbox",
        page=1,
        page_size=20,
    )
    imap_response = await imap_provider.list_messages(
        graph_credentials,
        folder="inbox",
        page=1,
        page_size=20,
    )

    assert graph_response.emails[0].message_id == "graph-message-id"
    assert imap_response.emails[0].message_id == "INBOX-1"
    assert imap_response.emails[0].message_id != graph_response.emails[0].message_id

    cache_service.email_list_cache.clear()
    cache_service.email_detail_cache.clear()
    db.clear_email_cache_db(email)


@pytest.mark.asyncio
async def test_graph_detail_skip_cache_bypasses_lru_and_db_cache(
    monkeypatch: pytest.MonkeyPatch,
):
    email = "graph-detail-skip-cache@example.com"
    message_id = "AAMkGraphDetailSkipCacheMessage"
    cache_service.email_list_cache.clear()
    cache_service.email_detail_cache.clear()
    db.clear_email_cache_db(email)

    cached_detail = {
        "message_id": message_id,
        "subject": "Cached graph subject",
        "from_email": "cached@example.com",
        "to_email": email,
        "date": "2026-04-30T00:00:00+00:00",
        "body_plain": "cached body 111111",
        "body_html": None,
        "verification_code": "111111",
    }
    fresh_detail = {
        "id": message_id,
        "subject": "Fresh graph subject",
        "from": {"emailAddress": {"address": "fresh@example.com"}},
        "toRecipients": [{"emailAddress": {"address": email}}],
        "receivedDateTime": "2026-04-30T00:01:00Z",
        "body": {"contentType": "text", "content": "fresh body 222222"},
        "bodyPreview": "fresh body 222222",
    }

    cache_service.set_cached_email_detail(
        email,
        message_id,
        cached_detail,
        provider="graph_api",
    )
    db.cache_email_detail(email, cached_detail, provider="graph_api")

    class FakeResponse:
        status_code = 200
        text = "ok"

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return fresh_detail

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            self.calls: list[tuple[str, dict]] = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, *, headers: dict, params: dict):
            self.calls.append((url, {"headers": headers, "params": params}))
            return FakeResponse()

    async def fake_get_graph_access_token(_credentials: AccountCredentials) -> str:
        return "graph-token"

    monkeypatch.setattr("graph_api_service.get_graph_access_token", fake_get_graph_access_token)
    monkeypatch.setattr("graph_api_service.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        "graph_api_service.detect_verification_code_with_rules",
        lambda **_kwargs: {},
    )

    gateway = MailGateway(
        graph_provider=graph_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )
    credentials = AccountCredentials(
        email=email,
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="graph_api",
        strategy_mode="graph_preferred",
    )

    response = await gateway.get_message_detail(
        credentials,
        message_id=message_id,
        override_provider="graph",
        skip_cache=True,
    )

    assert response.subject == "Fresh graph subject"
    assert response.body_plain == "fresh body 222222"
    assert response.from_email == "fresh@example.com"
    assert response.verification_code is None

    cache_service.email_list_cache.clear()
    cache_service.email_detail_cache.clear()
    db.clear_email_cache_db(email)


@pytest.mark.asyncio
async def test_mail_gateway_probe_runtime_error_does_not_silently_fallback(
    credentials,
    email_list_response,
):
    graph_fake_provider = FakeProvider(name="graph", list_response=email_list_response)
    imap_fake_provider = FakeProvider(name="imap", list_response=email_list_response)

    async def broken_graph_probe(_credentials: AccountCredentials) -> dict:
        raise RuntimeError("probe implementation bug")

    gateway = MailGateway(
        graph_provider=graph_fake_provider,
        imap_provider=imap_fake_provider,
        graph_probe=broken_graph_probe,
        persist_provider_hint=noop_persist_provider_hint,
    )
    credentials.api_method = ""
    credentials.last_provider_used = None

    with pytest.raises(RuntimeError, match="probe implementation bug"):
        await gateway.list_messages(
            credentials,
            folder="inbox",
            page=1,
            page_size=20,
            strategy_mode="auto",
        )

    assert graph_fake_provider.calls == []
    assert imap_fake_provider.calls == []


@pytest.mark.asyncio
async def test_mail_gateway_does_not_fallback_on_generic_http_500(
    credentials,
    email_list_response,
):
    graph_fake_provider = FakeProvider(
        name="graph",
        list_error=HTTPException(status_code=500, detail="graph internal error"),
    )
    imap_fake_provider = FakeProvider(name="imap", list_response=email_list_response)
    gateway = MailGateway(
        graph_provider=graph_fake_provider,
        imap_provider=imap_fake_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    with pytest.raises(HTTPException) as exc_info:
        await gateway.list_messages(
            credentials.model_copy(update={"api_method": "graph_api"}),
            folder="inbox",
            page=1,
            page_size=20,
            strategy_mode="graph_preferred",
        )

    assert exc_info.value.status_code == 500
    assert [call[0] for call in graph_fake_provider.calls] == ["list"]
    assert imap_fake_provider.calls == []


@pytest.mark.asyncio
async def test_mail_gateway_default_probe_path_does_not_swallow_runtime_bug(
    monkeypatch: pytest.MonkeyPatch,
    credentials,
    email_list_response,
):
    graph_fake_provider = FakeProvider(name="graph", list_response=email_list_response)
    imap_fake_provider = FakeProvider(name="imap", list_response=email_list_response)

    async def broken_fetch_access_token(self, credentials, *, persist, strategy_mode=None, requested_provider=None):
        raise RuntimeError("default probe runtime bug")

    monkeypatch.setattr(
        "graph_api_service.TokenBroker.fetch_access_token",
        broken_fetch_access_token,
    )

    gateway = MailGateway(
        graph_provider=graph_fake_provider,
        imap_provider=imap_fake_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )
    credentials.api_method = ""
    credentials.last_provider_used = None

    with pytest.raises(RuntimeError, match="default probe runtime bug"):
        await gateway.list_messages(
            credentials,
            folder="inbox",
            page=1,
            page_size=20,
            strategy_mode="auto",
        )

    assert graph_fake_provider.calls == []
    assert imap_fake_provider.calls == []


@pytest.mark.asyncio
async def test_mail_gateway_returns_success_when_persist_hint_fails(
    credentials,
    email_list_response,
):
    graph_fake_provider = FakeProvider(name="graph", list_response=email_list_response)
    imap_fake_provider = FakeProvider(name="imap", list_response=email_list_response)

    def fail_persist_provider_hint(_email: str, _provider_name: str) -> bool:
        return False

    gateway = MailGateway(
        graph_provider=graph_fake_provider,
        imap_provider=imap_fake_provider,
        persist_provider_hint=fail_persist_provider_hint,
    )

    response = await gateway.list_messages(
        credentials,
        folder="inbox",
        page=1,
        page_size=20,
        override_provider="imap",
    )

    assert response is email_list_response
    assert credentials.last_provider_used == "imap"
    assert [call[0] for call in imap_fake_provider.calls] == ["list"]


@pytest.mark.asyncio
async def test_mail_gateway_does_not_fallback_when_imap_direct_impl_has_bug(
    monkeypatch: pytest.MonkeyPatch,
    credentials,
    email_list_response,
):
    class FakeBrokenImapPool:
        def get_connection(self, email: str, access_token: str):
            raise RuntimeError("imap implementation bug")

    async def fake_get_cached_access_token(_credentials: AccountCredentials) -> str:
        return "token"

    monkeypatch.setattr("email_service.imap_pool", FakeBrokenImapPool())
    monkeypatch.setattr("email_service.get_cached_access_token", fake_get_cached_access_token)

    graph_fake_provider = FakeProvider(name="graph", list_response=email_list_response)

    gateway = MailGateway(
        graph_provider=graph_fake_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    with pytest.raises(RuntimeError, match="imap implementation bug"):
        await gateway.list_messages(
            credentials.model_copy(update={"api_method": "imap"}),
            folder="inbox",
            page=1,
            page_size=20,
            strategy_mode="imap_only",
        )

    assert graph_fake_provider.calls == []


@pytest.mark.asyncio
async def test_mail_gateway_does_not_fallback_when_imap_list_path_has_attribute_error(
    monkeypatch: pytest.MonkeyPatch,
    credentials,
    email_list_response,
):
    class FakeBrokenImapPool:
        def get_connection(self, email: str, access_token: str):
            raise AttributeError("imap list attribute bug")

    async def fake_get_cached_access_token(_credentials: AccountCredentials) -> str:
        return "token"

    monkeypatch.setattr("email_service.imap_pool", FakeBrokenImapPool())
    monkeypatch.setattr("email_service.get_cached_access_token", fake_get_cached_access_token)

    graph_fake_provider = FakeProvider(name="graph", list_response=email_list_response)

    gateway = MailGateway(
        graph_provider=graph_fake_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    with pytest.raises(AttributeError, match="imap list attribute bug"):
        await gateway.list_messages(
            credentials.model_copy(update={"api_method": "imap"}),
            folder="inbox",
            page=1,
            page_size=20,
            strategy_mode="imap_only",
        )

    assert graph_fake_provider.calls == []


@pytest.mark.asyncio
async def test_mail_gateway_does_not_fallback_when_imap_detail_path_has_attribute_error(
    monkeypatch: pytest.MonkeyPatch,
    credentials,
    email_detail_response,
):
    class FakeBrokenImapPool:
        def get_connection(self, email: str, access_token: str):
            raise AttributeError("imap detail attribute bug")

    async def fake_get_cached_access_token(_credentials: AccountCredentials) -> str:
        return "token"

    monkeypatch.setattr("email_service.imap_pool", FakeBrokenImapPool())
    monkeypatch.setattr("email_service.get_cached_access_token", fake_get_cached_access_token)

    graph_fake_provider = FakeProvider(name="graph", detail_response=email_detail_response)

    gateway = MailGateway(
        graph_provider=graph_fake_provider,
        imap_provider=imap_provider,
        persist_provider_hint=noop_persist_provider_hint,
    )

    with pytest.raises(AttributeError, match="imap detail attribute bug"):
        await gateway.get_message_detail(
            credentials.model_copy(update={"api_method": "imap"}),
            message_id="INBOX-1",
            strategy_mode="imap_only",
            skip_cache=True,
        )

    assert graph_fake_provider.calls == []
