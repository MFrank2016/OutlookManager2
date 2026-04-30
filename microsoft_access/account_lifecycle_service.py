from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

import database as db
from dao.account_dao import AccountDAO
from models import AccountCredentials, normalize_strategy_mode
from microsoft_access.capability_resolver import CapabilityResolver
from microsoft_access.mail_gateway import MailGateway, default_mail_gateway
from microsoft_access.token_broker import TokenBroker


AccountLoader = Callable[[str], Awaitable[AccountCredentials]]


class AccountLifecycleService:
    """统一处理账户预检、能力快照与读路径策略摘要。"""

    def __init__(
        self,
        *,
        token_broker: Optional[TokenBroker] = None,
        capability_resolver: Optional[CapabilityResolver] = None,
        mail_gateway: Optional[MailGateway] = None,
        account_loader: Optional[AccountLoader] = None,
        account_dao: Optional[AccountDAO] = None,
        db_module: Any = db,
        now_fn: Optional[Callable[[], datetime]] = None,
    ) -> None:
        if account_loader is None:
            from account_service import get_account_credentials

            account_loader = get_account_credentials

        self.token_broker = token_broker or TokenBroker()
        self.capability_resolver = capability_resolver or CapabilityResolver()
        self.mail_gateway = mail_gateway or default_mail_gateway
        self.account_loader = account_loader
        self.account_dao = account_dao or AccountDAO()
        self.db = db_module
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    async def register_account(self, credentials: AccountCredentials) -> Dict[str, Any]:
        token_result = await self.token_broker.fetch_access_token(
            credentials,
            persist=True,
            strategy_mode=getattr(credentials, "strategy_mode", None),
        )

        current_time = datetime.now().isoformat()
        next_refresh = datetime.now() + timedelta(days=7)
        if getattr(token_result, "refresh_token", None):
            credentials.refresh_token = token_result.refresh_token
        credentials.last_refresh_time = current_time
        credentials.next_refresh_time = next_refresh.isoformat()
        credentials.refresh_status = "success"
        credentials.refresh_error = None

        provider_hint = self._normalize_provider_name(
            getattr(token_result, "provider_hint", None)
        )
        if provider_hint is not None:
            credentials.api_method = provider_hint
            credentials.last_provider_used = provider_hint

        from account_service import save_account_credentials

        await save_account_credentials(credentials.email, credentials)
        return {
            "email_id": credentials.email,
            "message": "Account verified and saved successfully.",
        }

    async def refresh_account_token(self, email: str) -> Dict[str, Any]:
        credentials = await self.account_loader(email)
        result = await self.token_broker.refresh_access_token(
            credentials,
            persist=True,
            strategy_mode=getattr(credentials, "strategy_mode", None),
        )

        from account_service import save_account_credentials

        if result["success"]:
            current_time = datetime.now().isoformat()
            next_refresh = datetime.now() + timedelta(days=7)
            credentials.refresh_token = result["new_refresh_token"]
            credentials.last_refresh_time = current_time
            credentials.next_refresh_time = next_refresh.isoformat()
            credentials.refresh_status = "success"
            credentials.refresh_error = None
            await save_account_credentials(email, credentials)
            return {
                "success": True,
                "email_id": email,
                "message": f"Token refreshed successfully at {current_time}",
            }

        credentials.refresh_status = "failed"
        credentials.refresh_error = result.get("error", "Unknown error")
        await save_account_credentials(email, credentials)
        return {
            "success": False,
            "email_id": email,
            "error": result.get("error", "Unknown error"),
        }

    async def detect_api_method(self, email: str) -> Dict[str, Any]:
        await self.detect_capability(email, persist=True)
        credentials = await self.account_loader(email)
        provider_order = await self.mail_gateway.resolve_provider_order(
            credentials,
            strategy_mode=getattr(credentials, "strategy_mode", None),
            override_provider=None,
        )
        api_method = provider_order[0] if provider_order else "imap"
        self.db.update_account(email, api_method=api_method)
        return {"email_id": email, "api_method": api_method}

    async def probe_account(
        self,
        credentials: AccountCredentials,
        *,
        persist: bool = False,
    ) -> Dict[str, Any]:
        capability = await self.capability_resolver.detect_capability(
            credentials,
            persist=persist,
            probe_source="api_v2_probe",
        )
        if persist:
            self.account_dao.update_account(credentials.email, lifecycle_state="probed")

        graph_probe_status = capability.get("graph_probe_status")
        warnings: list[str] = []
        if graph_probe_status in {"probe_error", "insufficient_evidence"}:
            warnings.append("graph_read_capability_unknown")

        return {
            "token_ok": graph_probe_status != "probe_error",
            "capability": capability,
            "lifecycle_state": "probed",
            "warnings": warnings,
        }

    async def detect_capability(
        self,
        email: str,
        *,
        persist: bool = True,
    ) -> Dict[str, Any]:
        credentials = await self.account_loader(email)
        capability = await self.capability_resolver.detect_capability(
            credentials,
            persist=persist,
            probe_source="api_v2_capability_detection",
        )
        if persist:
            self.account_dao.update_account(email, lifecycle_state="probed")
        return capability

    async def get_account_health(self, email: str) -> Dict[str, Any]:
        credentials = await self.account_loader(email)
        capability = self._parse_json_object(credentials.capability_snapshot_json)
        provider_health = self._parse_json_object(credentials.provider_health_json)
        last_error = self._extract_last_error(provider_health)

        return {
            "email": credentials.email,
            "strategy_mode": credentials.strategy_mode or "auto",
            "lifecycle_state": credentials.lifecycle_state or "new",
            "capability": capability,
            "last_provider_used": self._normalize_provider_name(credentials.last_provider_used),
            "last_error": last_error,
        }

    async def resolve_delivery_strategy(
        self,
        email: str,
        *,
        strategy_mode: Optional[str] = None,
        override_provider: Optional[str] = None,
        skip_cache: bool = False,
    ) -> Dict[str, Any]:
        credentials = await self.account_loader(email)
        capability = self._parse_json_object(credentials.capability_snapshot_json)
        resolved_strategy_mode = normalize_strategy_mode(
            strategy_mode or credentials.strategy_mode
        ).value
        explicit_override = self._normalize_provider_name(override_provider)
        recommended_provider = self._normalize_provider_name(
            capability.get("recommended_provider")
        )
        if recommended_provider is None:
            recommended_provider_order = await self.mail_gateway.resolve_provider_order(
                credentials,
                strategy_mode=resolved_strategy_mode,
                override_provider=None,
            )
            recommended_provider = (
                recommended_provider_order[0] if recommended_provider_order else None
            )
        provider_order = await self.mail_gateway.resolve_provider_order(
            credentials,
            strategy_mode=resolved_strategy_mode,
            override_provider=override_provider,
        )
        resolved_provider = provider_order[0] if provider_order else None

        return {
            "email": credentials.email,
            "strategy_mode": resolved_strategy_mode,
            "recommended_provider": recommended_provider,
            "resolved_provider": resolved_provider,
            "provider_order": provider_order,
            "last_provider_used": self._normalize_provider_name(credentials.last_provider_used),
            "override_active": explicit_override is not None or skip_cache,
            "override_provider": explicit_override,
            "skip_cache": skip_cache,
            "capability": capability,
        }

    async def override_delivery_strategy(
        self,
        email: str,
        *,
        provider: Optional[str],
        strategy_mode: Optional[str] = None,
        skip_cache: bool = False,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        preview = await self.resolve_delivery_strategy(
            email,
            strategy_mode=strategy_mode,
            override_provider=provider,
            skip_cache=skip_cache,
        )
        requested_override: Dict[str, Any] = {
            "provider": provider,
            "skip_cache": skip_cache,
            "ttl_seconds": ttl_seconds,
        }
        if strategy_mode is not None:
            requested_override["strategy_mode"] = strategy_mode
        return {
            "preview_only": True,
            "persisted": False,
            "effective_for_future_requests": False,
            "message": "override preview only; no state was persisted",
            "requested_override": requested_override,
            "delivery_strategy_preview": preview,
        }

    def _parse_json_object(self, raw_value: Any) -> Dict[str, Any]:
        if raw_value in (None, ""):
            return {}
        if isinstance(raw_value, dict):
            return raw_value
        if isinstance(raw_value, str):
            try:
                parsed = json.loads(raw_value)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _extract_last_error(self, provider_health: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        direct_error = provider_health.get("last_error")
        if isinstance(direct_error, dict):
            return direct_error

        message = provider_health.get("last_error_message")
        code = provider_health.get("last_error_code")
        at = provider_health.get("last_error_at")
        if not any((message, code, at)):
            return None

        result: Dict[str, Any] = {}
        if code:
            result["code"] = code
        if message:
            result["message"] = message
        if at:
            result["at"] = at
        return result or None

    def _normalize_provider_name(self, provider_name: Optional[str]) -> Optional[str]:
        if provider_name is None:
            return None
        normalized = provider_name.strip().lower()
        if normalized in {"", "auto"}:
            return None
        if normalized in {"graph", "graph_api"}:
            return "graph_api"
        if normalized == "imap":
            return "imap"
        return None


__all__ = ["AccountLifecycleService"]
