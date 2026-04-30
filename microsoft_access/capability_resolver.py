from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from dao.account_dao import AccountDAO
from logger_config import logger
from models import AccountCredentials


GraphProbe = Callable[[AccountCredentials], Awaitable[Dict[str, Any]]]


class CapabilityResolver:
    """统一探测 Microsoft 账户可用 provider，并维护 capability 快照。"""

    def __init__(
        self,
        *,
        graph_probe: Optional[GraphProbe] = None,
        account_dao: Optional[AccountDAO] = None,
        now_fn: Optional[Callable[[], datetime]] = None,
        probe_source: str = "graph_probe",
    ) -> None:
        if graph_probe is None:
            from graph_api_service import check_graph_api_availability

            graph_probe = check_graph_api_availability

        self.graph_probe = graph_probe
        self.account_dao = account_dao or AccountDAO()
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self.probe_source = probe_source

    async def detect_capability(
        self,
        credentials: AccountCredentials,
        *,
        persist: bool = True,
        probe_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        graph_error: Optional[str] = None
        graph_capabilities = self._unknown_graph_capabilities()
        try:
            graph_result = await self.graph_probe(credentials)
            graph_available, graph_status, graph_capabilities = self._classify_graph_result(
                graph_result
            )
            if graph_status == "probe_error":
                graph_error = str(graph_result.get("error") or "graph_probe_error")
        except Exception as exc:
            logger.warning(
                "Capability graph probe failed for {}: {}",
                credentials.email,
                exc,
            )
            graph_available = None
            graph_status = "probe_error"
            graph_error = str(exc)

        snapshot = self._build_snapshot(
            graph_available=graph_available,
            graph_capabilities=graph_capabilities,
            probe_source=probe_source or self.probe_source,
            graph_status=graph_status,
            graph_error=graph_error,
        )

        if persist:
            persisted = self.account_dao.update_capability_snapshot(credentials.email, snapshot)
            if not persisted:
                raise RuntimeError(
                    f"Failed to persist capability snapshot for {credentials.email}"
                )

        credentials.capability_snapshot_json = json.dumps(snapshot, ensure_ascii=False)

        logger.info(
            "Capability detected for {}: graph_available={}, recommended_provider={}, graph_probe_status={}",
            credentials.email,
            snapshot["graph_available"],
            snapshot["recommended_provider"],
            snapshot["graph_probe_status"],
        )
        return snapshot

    def detect_capability_sync(
        self,
        credentials: AccountCredentials,
        *,
        persist: bool = True,
        probe_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        return asyncio.run(
            self.detect_capability(
                credentials,
                persist=persist,
                probe_source=probe_source,
            )
        )

    def _build_snapshot(
        self,
        *,
        graph_available: Optional[bool],
        graph_capabilities: Dict[str, Optional[bool]],
        probe_source: str,
        graph_status: str,
        graph_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {
            "graph_available": graph_available,
            **graph_capabilities,
            "imap_available": None,
            "recommended_provider": self._recommended_provider(graph_capabilities),
            "last_probe_at": self._now_isoformat(),
            "last_probe_source": probe_source,
            "graph_probe_status": graph_status,
        }
        if graph_error:
            snapshot["graph_probe_error"] = graph_error
        return snapshot

    def _classify_graph_result(
        self,
        graph_result: Optional[Dict[str, Any]],
    ) -> tuple[Optional[bool], str, Dict[str, Optional[bool]]]:
        if not graph_result:
            return None, "insufficient_evidence", self._unknown_graph_capabilities()

        if graph_result.get("error_category") == "probe_error":
            return None, "probe_error", self._unknown_graph_capabilities()

        fine_capabilities = self._extract_graph_capabilities(graph_result)
        if any(value is not None for value in fine_capabilities.values()):
            graph_available = graph_result.get("graph_available")
            if graph_available is None:
                graph_available = any(value is True for value in fine_capabilities.values())
            if graph_available is True:
                return True, "mail_scope_confirmed", fine_capabilities
            if graph_available is False:
                return False, "confirmed_unavailable", fine_capabilities

        explicit_capability = graph_result.get("mail_scope_granted")
        if explicit_capability is True:
            return True, "mail_scope_confirmed", self._capabilities_from_scope(
                graph_result.get("scope")
            )
        if explicit_capability is False:
            return False, "confirmed_unavailable", self._capabilities_from_scope(
                graph_result.get("scope")
            )

        scope = graph_result.get("scope")
        scope_capabilities = self._capabilities_from_scope(scope)
        if self._scope_has_any_mail_capability(scope):
            return True, "mail_scope_confirmed", scope_capabilities

        if graph_result.get("available") and graph_result.get("access_token"):
            return None, "insufficient_evidence", self._unknown_graph_capabilities()

        return None, "insufficient_evidence", self._unknown_graph_capabilities()

    def _recommended_provider(
        self,
        graph_capabilities: Dict[str, Optional[bool]],
    ) -> Optional[str]:
        if graph_capabilities.get("graph_read_available") is True:
            return "graph_api"
        if graph_capabilities.get("graph_read_available") is False:
            return "imap"
        return None

    def _unknown_graph_capabilities(self) -> Dict[str, Optional[bool]]:
        return {
            "graph_read_available": None,
            "graph_write_available": None,
            "graph_send_available": None,
        }

    def _extract_graph_capabilities(
        self,
        graph_result: Dict[str, Any],
    ) -> Dict[str, Optional[bool]]:
        keys = (
            "graph_read_available",
            "graph_write_available",
            "graph_send_available",
        )
        capabilities = {key: graph_result.get(key) for key in keys}
        if all(value is None for value in capabilities.values()):
            return self._unknown_graph_capabilities()
        return capabilities

    def _capabilities_from_scope(self, scope: Any) -> Dict[str, Optional[bool]]:
        if not isinstance(scope, str) or not scope.strip():
            return self._unknown_graph_capabilities()
        normalized_scope = scope.replace(",", " ")
        tokens = {token.strip() for token in normalized_scope.split() if token.strip()}
        read_available = bool(
            {
                "Mail.Read",
                "Mail.ReadWrite",
                "https://graph.microsoft.com/Mail.Read",
                "https://graph.microsoft.com/Mail.ReadWrite",
            }
            & tokens
        )
        write_available = bool(
            {
                "Mail.ReadWrite",
                "https://graph.microsoft.com/Mail.ReadWrite",
            }
            & tokens
        )
        send_available = bool(
            {
                "Mail.Send",
                "https://graph.microsoft.com/Mail.Send",
            }
            & tokens
        )
        return {
            "graph_read_available": read_available,
            "graph_write_available": write_available,
            "graph_send_available": send_available,
        }

    def _scope_has_any_mail_capability(self, scope: Any) -> bool:
        if not isinstance(scope, str) or not scope.strip():
            return False
        normalized_scope = scope.replace(",", " ")
        tokens = {token.strip() for token in normalized_scope.split() if token.strip()}
        allowed_mail_scopes = {
            "Mail.Read",
            "Mail.ReadWrite",
            "Mail.Send",
            "https://graph.microsoft.com/Mail.Read",
            "https://graph.microsoft.com/Mail.ReadWrite",
            "https://graph.microsoft.com/Mail.Send",
        }
        return bool(tokens & allowed_mail_scopes)

    def _now_isoformat(self) -> str:
        current = self.now_fn()
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        else:
            current = current.astimezone(timezone.utc)
        return current.isoformat()
