from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException

import oauth_service
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

    def update_account(self, email: str, **kwargs) -> bool:
        self.account_updates.append((email, kwargs))
        return True

    def update_account_access_token(
        self, email: str, access_token: str | None, expires_at: str | None
    ) -> bool:
        self.access_token_updates.append((email, access_token, expires_at))
        return True


class FakeCache:
    def __init__(self):
        self.storage = {}

    def get_access_token_cache_key(self, email: str):
        return ("access_token", email)

    def set_cached_access_token(
        self, email: str, access_token: str, expires_at: str | None = None
    ) -> None:
        self.storage[self.get_access_token_cache_key(email)] = {
            "access_token": access_token,
            "expires_at": expires_at,
        }

    def clear_cached_access_token(self, email: str) -> None:
        self.storage.pop(self.get_access_token_cache_key(email), None)


class RaisingBroker:
    def __init__(self, exc: Exception):
        self.exc = exc

    async def fetch_access_token(self, *_args, **_kwargs):
        raise self.exc

    async def get_cached_access_token(self, *_args, **_kwargs):
        raise self.exc

    async def refresh_access_token(self, *_args, **_kwargs):
        raise self.exc

    async def clear_cached_access_token(self, *_args, **_kwargs):
        raise self.exc


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 4, 30, 1, 2, 3, tzinfo=timezone.utc)


@pytest.fixture
def credentials() -> AccountCredentials:
    return AccountCredentials(
        email="refresh-test@example.com",
        refresh_token="refresh-token",
        client_id="client-id",
        api_method="imap",
        strategy_mode="auto",
    )


def test_token_refresh_module_is_not_live_only_anymore():
    conftest = importlib.import_module("conftest")

    assert "test_token_refresh.py" not in conftest.LIVE_TEST_FILES


@pytest.mark.asyncio
async def test_refresh_access_token_returns_new_tokens_and_expiry(
    credentials: AccountCredentials, fixed_now: datetime
):
    request_log: list[dict] = []
    broker = TokenBroker(
        db_module=FakeDB(),
        cache_module=FakeCache(),
        http_client_factory=lambda timeout=30.0: FakeAsyncClient(
            [
                FakeResponse(
                    200,
                    {
                        "access_token": "new-access-token",
                        "refresh_token": "new-refresh-token",
                        "expires_in": 1800,
                    },
                )
            ],
            request_log,
        ),
        now_fn=lambda: fixed_now,
    )

    result = await broker.refresh_access_token(credentials)

    assert result["success"] is True
    assert result["new_access_token"] == "new-access-token"
    assert result["new_refresh_token"] == "new-refresh-token"
    assert result["access_token_expires_at"] == "2026-04-30T01:32:03+00:00"
    assert request_log == [
        {
            "client_id": "client-id",
            "grant_type": "refresh_token",
            "refresh_token": "refresh-token",
            "scope": "https://outlook.office.com/IMAP.AccessAsUser.All offline_access",
        }
    ]


@pytest.mark.asyncio
async def test_refresh_access_token_reuses_existing_refresh_token_when_missing(
    credentials: AccountCredentials, fixed_now: datetime
):
    broker = TokenBroker(
        db_module=FakeDB(),
        cache_module=FakeCache(),
        http_client_factory=lambda timeout=30.0: FakeAsyncClient(
            [
                FakeResponse(
                    200,
                    {
                        "access_token": "new-access-token",
                        "expires_in": 1800,
                    },
                )
            ],
            [],
        ),
        now_fn=lambda: fixed_now,
    )

    result = await broker.refresh_access_token(credentials)

    assert result["success"] is True
    assert result["new_refresh_token"] == "refresh-token"


@pytest.mark.asyncio
async def test_oauth_service_get_access_token_wraps_request_error(monkeypatch):
    request = httpx.Request("POST", "https://login.microsoftonline.com")
    monkeypatch.setattr(
        oauth_service,
        "_token_broker",
        RaisingBroker(httpx.RequestError("boom", request=request)),
    )

    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.get_access_token(
            AccountCredentials(
                email="facade@example.com",
                refresh_token="rt",
                client_id="cid",
            )
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Network error during token acquisition"


@pytest.mark.asyncio
async def test_oauth_service_get_cached_access_token_wraps_request_error(monkeypatch):
    request = httpx.Request("POST", "https://login.microsoftonline.com")
    monkeypatch.setattr(
        oauth_service,
        "_token_broker",
        RaisingBroker(httpx.RequestError("boom", request=request)),
    )

    with pytest.raises(HTTPException) as exc_info:
        await oauth_service.get_cached_access_token(
            AccountCredentials(
                email="facade@example.com",
                refresh_token="rt",
                client_id="cid",
            )
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Network error during token acquisition"


@pytest.mark.asyncio
async def test_oauth_service_refresh_account_token_wraps_request_error(monkeypatch):
    request = httpx.Request("POST", "https://login.microsoftonline.com")
    monkeypatch.setattr(
        oauth_service,
        "_token_broker",
        RaisingBroker(httpx.RequestError("boom", request=request)),
    )

    result = await oauth_service.refresh_account_token(
        AccountCredentials(
            email="facade@example.com",
            refresh_token="rt",
            client_id="cid",
        )
    )

    assert result == {
        "success": False,
        "error": "Network error refreshing token: boom",
    }


@pytest.mark.asyncio
async def test_oauth_service_clear_cached_access_token_returns_false_on_unexpected_error(
    monkeypatch,
):
    monkeypatch.setattr(oauth_service, "_token_broker", RaisingBroker(RuntimeError("boom")))

    result = await oauth_service.clear_cached_access_token("facade@example.com")

    assert result is False


async def run_live_token_refresh_smoke(accounts_file: str = "accounts.json") -> None:
    """手动 live smoke helper，不参与默认 pytest。"""
    token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    oauth_scope = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access"
    accounts_path = Path(accounts_file)
    if not accounts_path.exists():
        raise FileNotFoundError(f"未找到 {accounts_file}")

    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    if not accounts:
        raise ValueError("accounts.json 中没有账户")

    email_id = next(iter(accounts))
    account_data = accounts[email_id]
    token_request_data = {
        "client_id": account_data["client_id"],
        "grant_type": "refresh_token",
        "refresh_token": account_data["refresh_token"],
        "scope": oauth_scope,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(token_url, data=token_request_data)
        response.raise_for_status()
        payload = response.json()

    if "access_token" not in payload:
        raise RuntimeError("响应缺少 access_token")

    print(json.dumps({"email": email_id, "keys": sorted(payload.keys())}, ensure_ascii=False))
