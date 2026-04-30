from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

import httpx
from fastapi import HTTPException

import cache_service
import database as db
from config import GRAPH_API_SCOPE, OAUTH_SCOPE, TOKEN_URL
from logger_config import logger
from models import AccountCredentials, normalize_strategy_mode


@dataclass(frozen=True)
class ScopePlan:
    primary_scope: str
    fallback_scope: Optional[str]
    provider_hint: str
    primary_provider: str
    fallback_provider: Optional[str]


@dataclass(frozen=True)
class AccessTokenResult:
    access_token: str
    expires_at: str
    expires_in: int
    provider_hint: str
    refresh_token: Optional[str] = None


class TokenBroker:
    """统一管理 Microsoft access token 的获取、缓存与 fallback。"""

    def __init__(
        self,
        *,
        db_module: Any = db,
        cache_module: Any = cache_service,
        http_client_factory: Optional[Callable[..., Any]] = None,
        now_fn: Optional[Callable[[], datetime]] = None,
        token_url: str = TOKEN_URL,
    ) -> None:
        self.db = db_module
        self.cache = cache_module
        self.http_client_factory = http_client_factory or (
            lambda timeout=30.0: httpx.AsyncClient(timeout=timeout)
        )
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self.token_url = token_url

    def build_scope_plan(
        self,
        *,
        strategy_mode: Optional[str],
        requested_provider: Optional[str],
        api_method: Optional[str] = None,
    ) -> ScopePlan:
        strategy = normalize_strategy_mode(strategy_mode).value
        explicit_provider = self._normalize_requested_provider(requested_provider)
        legacy_provider = self._normalize_stored_provider(api_method)

        if explicit_provider is not None:
            primary_provider = explicit_provider
            fallback_provider = None
        elif strategy == "graph_only":
            primary_provider = "graph_api"
            fallback_provider = None
        elif strategy == "imap_only":
            primary_provider = "imap"
            fallback_provider = None
        elif strategy == "graph_preferred":
            primary_provider = "graph_api"
            fallback_provider = self._alternate_provider(primary_provider)
        else:
            primary_provider = legacy_provider or "imap"
            fallback_provider = self._alternate_provider(primary_provider)

        return ScopePlan(
            primary_scope=self._scope_for_provider(primary_provider),
            fallback_scope=self._scope_for_provider(fallback_provider),
            provider_hint=primary_provider,
            primary_provider=primary_provider,
            fallback_provider=fallback_provider,
        )

    async def fetch_access_token(
        self,
        credentials: AccountCredentials,
        *,
        persist: bool,
        strategy_mode: Optional[str] = None,
        requested_provider: Optional[str] = None,
    ) -> AccessTokenResult:
        plan = self.build_scope_plan(
            strategy_mode=strategy_mode or getattr(credentials, "strategy_mode", "auto"),
            requested_provider=requested_provider,
            api_method=getattr(credentials, "api_method", None),
        )

        logger.info(
            f"Fetching access token for {credentials.email}, primary provider: {plan.primary_provider}"
        )

        try:
            response = await self._request_token(credentials, plan.primary_scope)
            used_provider = plan.primary_provider
            fallback_used = False

            if self._should_try_fallback(response, plan):
                logger.warning(
                    f"Token request failed with scope {plan.primary_scope}, trying fallback scope {plan.fallback_scope}"
                )
                response = await self._request_token(credentials, plan.fallback_scope)
                if response.status_code == 200 and plan.fallback_provider:
                    used_provider = plan.fallback_provider
                    fallback_used = True

            token_data = self._raise_for_invalid_token_response(credentials, response)
            result = self._build_token_result(token_data, used_provider)

            if persist:
                self._persist_access_token(
                    credentials.email,
                    result.access_token,
                    result.expires_at,
                )
                self._persist_provider_hint(
                    credentials,
                    provider_hint=used_provider,
                    force=fallback_used,
                )

            return result
        except httpx.RequestError as exc:
            logger.error(f"Request error getting access token for {credentials.email}: {exc}")
            raise HTTPException(
                status_code=500,
                detail="Network error during token acquisition",
            )

    async def get_cached_access_token(self, credentials: AccountCredentials) -> str:
        email = credentials.email

        memory_token = self._get_valid_memory_token(email)
        if memory_token:
            return memory_token

        token_info = self.db.get_account_access_token(email)
        if token_info:
            access_token = token_info.get("access_token")
            expires_at = token_info.get("token_expires_at")
            if access_token and self._is_token_valid(expires_at):
                expires_at_str = self._normalize_expires_at_for_cache(expires_at)
                self.cache.set_cached_access_token(email, access_token, expires_at_str)
                logger.info(f"Using database cached access token for {email}")
                return access_token

        logger.info(f"Fetching new access token for {email}")
        result = await self.fetch_access_token(credentials, persist=True)
        return result.access_token

    async def refresh_access_token(
        self,
        credentials: AccountCredentials,
        *,
        persist: bool = False,
        strategy_mode: Optional[str] = None,
        requested_provider: Optional[str] = None,
    ) -> dict:
        plan = self.build_scope_plan(
            strategy_mode=strategy_mode or getattr(credentials, "strategy_mode", "auto"),
            requested_provider=requested_provider,
            api_method=getattr(credentials, "api_method", None),
        )

        try:
            response = await self._request_token(credentials, plan.primary_scope)
            used_provider = plan.primary_provider
            fallback_used = False

            if self._should_try_fallback(response, plan):
                logger.warning(
                    f"Token refresh failed with scope {plan.primary_scope}, trying fallback scope {plan.fallback_scope} for {credentials.email}"
                )
                response = await self._request_token(credentials, plan.fallback_scope)
                if response.status_code == 200 and plan.fallback_provider:
                    used_provider = plan.fallback_provider
                    fallback_used = True

            token_data = self._raise_for_invalid_token_response(
                credentials,
                response,
                raise_http=False,
            )
            if not token_data:
                return {
                    "success": False,
                    "error": f"OAuth2 Error: {self._extract_error_description(response, 'Invalid grant')}",
                }

            result = self._build_token_result(token_data, used_provider)
            new_refresh_token = token_data.get("refresh_token") or credentials.refresh_token
            if persist:
                self._persist_access_token(
                    credentials.email,
                    result.access_token,
                    result.expires_at,
                )
                self._persist_provider_hint(
                    credentials,
                    provider_hint=used_provider,
                    force=fallback_used,
                )

            return {
                "success": True,
                "new_refresh_token": new_refresh_token,
                "new_access_token": result.access_token,
                "access_token_expires_at": result.expires_at,
            }
        except httpx.RequestError as exc:
            error_msg = f"Network error refreshing token: {str(exc)}"
            logger.error(f"{error_msg} for {credentials.email}")
            return {"success": False, "error": error_msg}
        except HTTPException as exc:
            return {"success": False, "error": str(exc.detail)}
        except Exception as exc:
            error_msg = f"Unexpected error: {str(exc)}"
            logger.error(f"{error_msg} for {credentials.email}")
            return {"success": False, "error": error_msg}

    async def clear_cached_access_token(self, email: str) -> bool:
        try:
            self.cache.clear_cached_access_token(email)
            success = self.db.update_account_access_token(email, None, None)
            if success:
                logger.info(
                    f"Cleared cached access token for {email} (both memory and database)"
                )
            return success
        except Exception as exc:
            logger.error(f"Error clearing cached token for {email}: {exc}")
            return False

    def _normalize_requested_provider(self, provider: Optional[str]) -> Optional[str]:
        if provider is None:
            return None
        normalized = provider.strip().lower()
        if normalized in {"", "auto"}:
            return None
        if normalized in {"graph", "graph_api"}:
            return "graph_api"
        if normalized == "imap":
            return "imap"
        return None

    def _normalize_stored_provider(self, provider: Optional[str]) -> Optional[str]:
        if not provider:
            return None
        normalized = provider.strip().lower()
        if normalized in {"graph", "graph_api"}:
            return "graph_api"
        if normalized == "imap":
            return "imap"
        return "imap"

    def _alternate_provider(self, provider: Optional[str]) -> Optional[str]:
        normalized = self._normalize_stored_provider(provider)
        if normalized == "graph_api":
            return "imap"
        if normalized == "imap":
            return "graph_api"
        return None

    def _scope_for_provider(self, provider: Optional[str]) -> Optional[str]:
        normalized = self._normalize_stored_provider(provider)
        if normalized == "graph_api":
            return GRAPH_API_SCOPE
        if normalized == "imap":
            return OAUTH_SCOPE
        return None

    async def _request_token(self, credentials: AccountCredentials, scope: Optional[str]):
        token_request_data = {
            "client_id": credentials.client_id,
            "grant_type": "refresh_token",
            "refresh_token": credentials.refresh_token,
            "scope": scope,
        }
        async with self.http_client_factory(timeout=30.0) as client:
            return await client.post(self.token_url, data=token_request_data)

    def _should_try_fallback(self, response: Any, plan: ScopePlan) -> bool:
        return bool(
            plan.fallback_scope
            and response.status_code == 400
            and self._is_scope_related_error(response)
        )

    def _is_scope_related_error(self, response: Any) -> bool:
        error_description = self._extract_error_description(response, "")
        return "AADSTS70000" in error_description or "scope" in error_description.lower()

    def _extract_error_description(self, response: Any, default: str) -> str:
        try:
            payload = response.json()
        except Exception:
            return default
        return payload.get("error_description") or payload.get("error") or default

    def _raise_for_invalid_token_response(
        self,
        credentials: AccountCredentials,
        response: Any,
        *,
        raise_http: bool = True,
    ) -> Optional[dict]:
        if response.status_code in {400, 401, 403}:
            error_detail = (
                f"OAuth2 Error: {self._extract_error_description(response, 'Invalid grant')}"
            )
            logger.error(
                f"OAuth2 token request failed for {credentials.email}: {error_detail}"
            )
            if raise_http:
                raise HTTPException(status_code=400, detail=error_detail)
            return None
        if response.status_code >= 400:
            logger.error(
                f"HTTP {response.status_code} error getting access token for {credentials.email}: {getattr(response, 'text', '')}"
            )
            if raise_http:
                raise HTTPException(status_code=401, detail="Authentication failed")
            return None

        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            logger.error(f"No access token in response for {credentials.email}")
            if raise_http:
                raise HTTPException(
                    status_code=401,
                    detail="Failed to obtain access token from response",
                )
            return None
        return token_data

    def _build_token_result(self, token_data: dict, provider_hint: str) -> AccessTokenResult:
        expires_in = int(token_data.get("expires_in", 3600) or 3600)
        actual_expires_in = min(expires_in, 3 * 3600)
        expires_at = self.now_fn() + timedelta(seconds=actual_expires_in)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return AccessTokenResult(
            access_token=token_data["access_token"],
            expires_at=expires_at.isoformat(),
            expires_in=actual_expires_in,
            provider_hint=provider_hint,
            refresh_token=token_data.get("refresh_token"),
        )

    def _persist_access_token(self, email: str, access_token: str, expires_at: str) -> None:
        self.db.update_account_access_token(email, access_token, expires_at)
        self.cache.set_cached_access_token(email, access_token, expires_at)

    def _persist_provider_hint(
        self,
        credentials: AccountCredentials,
        *,
        provider_hint: str,
        force: bool,
    ) -> None:
        normalized_hint = self._normalize_stored_provider(provider_hint) or "imap"
        updates = {"last_provider_used": normalized_hint}
        credentials.last_provider_used = normalized_hint

        current_api_method = self._normalize_stored_provider(
            getattr(credentials, "api_method", None)
        )
        if current_api_method is None or (force and current_api_method != normalized_hint):
            updates["api_method"] = normalized_hint
            credentials.api_method = normalized_hint

        self.db.update_account(credentials.email, **updates)

    def _get_valid_memory_token(self, email: str) -> Optional[str]:
        cache_key_builder = getattr(self.cache, "get_access_token_cache_key", None)
        token_cache = getattr(self.cache, "access_token_cache", None)
        if not cache_key_builder or token_cache is None:
            return None

        cache_key = cache_key_builder(email)
        if cache_key not in token_cache:
            return None

        token_data = token_cache[cache_key]
        if isinstance(token_data, str):
            return token_data
        if not isinstance(token_data, dict):
            return None

        cached_token = token_data.get("access_token")
        expires_at = token_data.get("expires_at")
        if cached_token and not expires_at:
            return cached_token
        if cached_token and self._is_token_valid(expires_at):
            return cached_token

        self.cache.clear_cached_access_token(email)
        return None

    def _is_token_valid(self, expires_at: Any, *, refresh_buffer_seconds: int = 600) -> bool:
        try:
            expires_at_dt = self._coerce_datetime(expires_at)
        except Exception:
            return False
        now = self.now_fn()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return (expires_at_dt - now).total_seconds() > refresh_buffer_seconds

    def _normalize_expires_at_for_cache(self, expires_at: Any) -> str:
        return self._coerce_datetime(expires_at).isoformat()

    def _coerce_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
