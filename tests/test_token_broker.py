from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from config import GRAPH_API_SCOPE, OAUTH_SCOPE
from microsoft_access.token_broker import TokenBroker
from models import AccountCredentials


@dataclass
class FakeResponse:
    status_code: int
    payload: dict

    def json(self) -> dict:
        return self.payload

    @property
    def text(self) -> str:
        return str(self.payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"unexpected status {self.status_code}")


class FakeAsyncClient:
    def __init__(self, responses: list[FakeResponse], request_log: list[dict]):
        self._responses = responses
        self._request_log = request_log

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, _url: str, data: dict):
        self._request_log.append(data)
        if not self._responses:
            raise AssertionError("no fake response left")
        return self._responses.pop(0)


class FakeDB:
    def __init__(self):
        self.account_updates: list[tuple[str, dict]] = []
        self.access_token_updates: list[tuple[str, str | None, str | None]] = []
        self.cached_token = None

    def update_account(self, email: str, **kwargs) -> bool:
        self.account_updates.append((email, kwargs))
        return True

    def update_account_access_token(
        self, email: str, access_token: str | None, expires_at: str | None
    ) -> bool:
        self.access_token_updates.append((email, access_token, expires_at))
        return True

    def get_account_access_token(self, _email: str):
        return self.cached_token


class FakeCache:
    def __init__(self):
        self.storage = {}
        self.set_calls: list[tuple[str, str, str | None]] = []
        self.clear_calls: list[str] = []

    def get_access_token_cache_key(self, email: str):
        return ("access_token", email)

    def set_cached_access_token(
        self, email: str, access_token: str, expires_at: str | None = None
    ) -> None:
        self.storage[self.get_access_token_cache_key(email)] = {
            "access_token": access_token,
            "expires_at": expires_at,
        }
        self.set_calls.append((email, access_token, expires_at))

    def clear_cached_access_token(self, email: str) -> None:
        self.storage.pop(self.get_access_token_cache_key(email), None)
        self.clear_calls.append(email)


@pytest.fixture
def fixed_now():
    return datetime(2026, 4, 30, 1, 2, 3, tzinfo=timezone.utc)


@pytest.fixture
def credentials() -> AccountCredentials:
    return AccountCredentials(
        email="token-broker@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="auto",
    )


def test_choose_primary_scope_for_auto_defaults_to_imap():
    broker = TokenBroker()

    decision = broker.build_scope_plan(strategy_mode="auto", requested_provider=None)

    assert decision.primary_scope == OAUTH_SCOPE
    assert decision.fallback_scope == GRAPH_API_SCOPE
    assert decision.provider_hint == "imap"


def test_requested_provider_auto_matches_no_override_behavior():
    broker = TokenBroker()

    without_override = broker.build_scope_plan(
        strategy_mode="auto",
        requested_provider=None,
        api_method="graph_api",
    )
    explicit_auto = broker.build_scope_plan(
        strategy_mode="auto",
        requested_provider="auto",
        api_method="graph_api",
    )

    assert explicit_auto == without_override
    assert explicit_auto.primary_scope == GRAPH_API_SCOPE


def test_requested_provider_graph_is_explicit_override_without_fallback():
    broker = TokenBroker()

    decision = broker.build_scope_plan(
        strategy_mode="auto",
        requested_provider="graph",
        api_method="imap",
    )

    assert decision.primary_scope == GRAPH_API_SCOPE
    assert decision.fallback_scope is None
    assert decision.provider_hint == "graph_api"


def test_requested_provider_imap_is_explicit_override_without_fallback():
    broker = TokenBroker()

    decision = broker.build_scope_plan(
        strategy_mode="graph_preferred",
        requested_provider="imap",
        api_method="graph_api",
    )

    assert decision.primary_scope == OAUTH_SCOPE
    assert decision.fallback_scope is None
    assert decision.provider_hint == "imap"


@pytest.mark.asyncio
async def test_fallback_to_graph_scope_updates_provider_hint(
    credentials: AccountCredentials, fixed_now: datetime
):
    fake_db = FakeDB()
    fake_cache = FakeCache()
    request_log: list[dict] = []
    responses = [
        FakeResponse(
            400,
            {
                "error": "invalid_scope",
                "error_description": "AADSTS70000: unauthorized_scope",
            },
        ),
        FakeResponse(
            200,
            {
                "access_token": "graph-token",
                "expires_in": 1800,
            },
        ),
    ]

    broker = TokenBroker(
        db_module=fake_db,
        cache_module=fake_cache,
        http_client_factory=lambda timeout=30.0: FakeAsyncClient(responses, request_log),
        now_fn=lambda: fixed_now,
    )

    result = await broker.fetch_access_token(credentials, persist=True)

    assert result.access_token == "graph-token"
    assert result.provider_hint == "graph_api"
    assert request_log[0]["scope"] == OAUTH_SCOPE
    assert request_log[1]["scope"] == GRAPH_API_SCOPE
    assert fake_db.account_updates == [
        (
            credentials.email,
            {"api_method": "graph_api", "last_provider_used": "graph_api"},
        )
    ]
    assert credentials.api_method == "graph_api"
    assert credentials.last_provider_used == "graph_api"


@pytest.mark.asyncio
async def test_probe_mode_does_not_persist_access_token(
    credentials: AccountCredentials, fixed_now: datetime
):
    fake_db = FakeDB()
    fake_cache = FakeCache()
    request_log: list[dict] = []
    responses = [
        FakeResponse(
            200,
            {
                "access_token": "probe-token",
                "expires_in": 1800,
            },
        )
    ]

    broker = TokenBroker(
        db_module=fake_db,
        cache_module=fake_cache,
        http_client_factory=lambda timeout=30.0: FakeAsyncClient(responses, request_log),
        now_fn=lambda: fixed_now,
    )

    result = await broker.fetch_access_token(credentials, persist=False)

    assert result.access_token == "probe-token"
    assert request_log[0]["scope"] == OAUTH_SCOPE
    assert fake_db.access_token_updates == []
    assert fake_db.account_updates == []
    assert fake_cache.set_calls == []


@pytest.mark.asyncio
async def test_refresh_with_persist_false_does_not_update_account_state_on_fallback(
    credentials: AccountCredentials, fixed_now: datetime
):
    fake_db = FakeDB()
    request_log: list[dict] = []
    responses = [
        FakeResponse(
            400,
            {
                "error": "invalid_scope",
                "error_description": "AADSTS70000: unauthorized_scope",
            },
        ),
        FakeResponse(
            200,
            {
                "access_token": "graph-token",
                "refresh_token": "rotated-refresh-token",
                "expires_in": 1800,
            },
        ),
    ]
    credentials.last_provider_used = "imap"

    broker = TokenBroker(
        db_module=fake_db,
        cache_module=FakeCache(),
        http_client_factory=lambda timeout=30.0: FakeAsyncClient(responses, request_log),
        now_fn=lambda: fixed_now,
    )

    result = await broker.refresh_access_token(credentials, persist=False)

    assert result["success"] is True
    assert request_log[0]["scope"] == OAUTH_SCOPE
    assert request_log[1]["scope"] == GRAPH_API_SCOPE
    assert fake_db.access_token_updates == []
    assert fake_db.account_updates == []
    assert credentials.api_method == "imap"
    assert credentials.last_provider_used == "imap"


@pytest.mark.asyncio
async def test_persisted_fetch_updates_last_provider_used_even_when_provider_is_unchanged(
    credentials: AccountCredentials, fixed_now: datetime
):
    fake_db = FakeDB()
    credentials.api_method = "imap"
    credentials.last_provider_used = "imap"

    broker = TokenBroker(
        db_module=fake_db,
        cache_module=FakeCache(),
        http_client_factory=lambda timeout=30.0: FakeAsyncClient(
            [
                FakeResponse(
                    200,
                    {
                        "access_token": "imap-token",
                        "expires_in": 1800,
                    },
                )
            ],
            [],
        ),
        now_fn=lambda: fixed_now,
    )

    result = await broker.fetch_access_token(credentials, persist=True)

    assert result.provider_hint == "imap"
    assert fake_db.account_updates == [
        (
            credentials.email,
            {"last_provider_used": "imap"},
        )
    ]
    assert credentials.api_method == "imap"
    assert credentials.last_provider_used == "imap"
