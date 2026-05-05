from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Callable

import database as db
import httpx
from fastapi import HTTPException

from logger_config import logger
from models import (
    AccountCredentials,
    EmailDetailsResponse,
    EmailListResponse,
    normalize_strategy_mode,
)
from microsoft_access.providers import graph_provider, imap_provider


RECOVERABLE_PROVIDER_HTTP_STATUS_CODES = {401, 403, 408, 429, 502, 503, 504}
RECOVERABLE_PROVIDER_EXCEPTION_TYPES = (ConnectionError, TimeoutError)
RECOVERABLE_GRAPH_PROBE_HTTP_STATUS_CODES = {401, 403, 408, 429, 502, 503, 504}
RECOVERABLE_GRAPH_PROBE_EXCEPTION_TYPES = (
    ConnectionError,
    TimeoutError,
    httpx.TransportError,
    httpx.TimeoutException,
)
PersistProviderHint = Callable[[str, str], bool]
DETAIL_FETCH_CONCURRENCY_LIMIT = 5
DETAIL_HYDRATION_MAX_ITEMS = 50
DETAIL_PREVIEW_MAX_LENGTH = 180


class MailGateway:
    """统一 Microsoft 邮件读路径 provider 选路。"""

    def __init__(
        self,
        *,
        graph_provider: Any = graph_provider,
        imap_provider: Any = imap_provider,
        graph_probe: Any | None = None,
        persist_provider_hint: PersistProviderHint | None = None,
    ) -> None:
        self.graph_provider = graph_provider
        self.imap_provider = imap_provider
        self.graph_probe = graph_probe
        self.persist_provider_hint = persist_provider_hint or self._persist_provider_hint

    async def list_messages(
        self,
        credentials: AccountCredentials,
        *,
        folder: str,
        page: int,
        page_size: int,
        strategy_mode: str | None = None,
        override_provider: str | None = None,
        hydrate_details: bool = False,
        skip_cache: bool = False,
        sender_search: str | None = None,
        subject_search: str | None = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> EmailListResponse:
        last_error: Exception | None = None
        provider_order = await self.resolve_provider_order(
            credentials,
            strategy_mode=strategy_mode,
            override_provider=override_provider,
        )

        for provider_name in provider_order:
            provider = self._provider_for(provider_name)
            try:
                response = await provider.list_messages(
                    credentials,
                    folder=folder,
                    page=page,
                    page_size=page_size,
                    skip_cache=skip_cache,
                    sender_search=sender_search,
                    subject_search=subject_search,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    start_time=start_time,
                    end_time=end_time,
                )
                if hydrate_details:
                    response = await self._hydrate_list_response(
                        provider,
                        credentials,
                        response,
                        skip_cache=skip_cache,
                    )
                self._record_successful_provider(credentials, provider_name)
                return response
            except HTTPException as exc:
                if not self._is_recoverable_http_exception(exc):
                    raise
                last_error = exc
                logger.warning(
                    "MailGateway list_messages recoverable failure via {} for {}: {}",
                    provider_name,
                    credentials.email,
                    exc,
                )
                if provider_name == provider_order[-1]:
                    raise
            except RECOVERABLE_PROVIDER_EXCEPTION_TYPES as exc:
                last_error = exc
                logger.warning(
                    "MailGateway list_messages recoverable failure via {} for {}: {}",
                    provider_name,
                    credentials.email,
                    exc,
                )
                if provider_name == provider_order[-1]:
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("MailGateway failed to resolve provider for list_messages")

    async def get_message_detail(
        self,
        credentials: AccountCredentials,
        message_id: str,
        *,
        strategy_mode: str | None = None,
        override_provider: str | None = None,
        skip_cache: bool = False,
    ) -> EmailDetailsResponse:
        provider_order = await self.resolve_provider_order(
            credentials,
            strategy_mode=strategy_mode,
            override_provider=override_provider,
        )
        provider_name = provider_order[0]
        provider = self._provider_for(provider_name)
        response = await provider.get_message_detail(
            credentials,
            message_id,
            skip_cache=skip_cache,
        )
        self._record_successful_provider(credentials, provider_name)
        return response

    async def list_messages_with_body(
        self,
        credentials: AccountCredentials,
        *,
        folder: str,
        page: int,
        page_size: int,
        strategy_mode: str | None = None,
        override_provider: str | None = None,
        skip_cache: bool = False,
        sender_search: str | None = None,
        subject_search: str | None = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        last_error: Exception | None = None
        provider_order = await self.resolve_provider_order(
            credentials,
            strategy_mode=strategy_mode,
            override_provider=override_provider,
        )
        for provider_name in provider_order:
            provider = self._provider_for(provider_name)
            try:
                response = await self._list_messages_with_body_via_provider(
                    provider,
                    credentials,
                    folder=folder,
                    page=page,
                    page_size=page_size,
                    skip_cache=skip_cache,
                    sender_search=sender_search,
                    subject_search=subject_search,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    start_time=start_time,
                    end_time=end_time,
                )
                self._record_successful_provider(credentials, provider_name)
                return response
            except HTTPException as exc:
                if not self._is_recoverable_http_exception(exc):
                    raise
                last_error = exc
                logger.warning(
                    "MailGateway list_messages_with_body recoverable failure via {} for {}: {}",
                    provider_name,
                    credentials.email,
                    exc,
                )
                if provider_name == provider_order[-1]:
                    raise
            except RECOVERABLE_PROVIDER_EXCEPTION_TYPES as exc:
                last_error = exc
                logger.warning(
                    "MailGateway list_messages_with_body recoverable failure via {} for {}: {}",
                    provider_name,
                    credentials.email,
                    exc,
                )
                if provider_name == provider_order[-1]:
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("MailGateway failed to resolve provider for list_messages_with_body")

    async def delete_message(
        self,
        credentials: AccountCredentials,
        message_id: str,
        *,
        strategy_mode: str | None = None,
        override_provider: str | None = None,
    ) -> bool:
        provider_order = await self.resolve_provider_order(
            credentials,
            strategy_mode=strategy_mode,
            override_provider=override_provider,
        )
        provider_name = provider_order[0]
        provider = self._provider_for(provider_name)
        response = await provider.delete_message(credentials, message_id)
        self._record_successful_provider(credentials, provider_name)
        return response

    async def delete_messages_batch(
        self,
        credentials: AccountCredentials,
        *,
        folder: str,
        strategy_mode: str | None = None,
        override_provider: str | None = None,
    ) -> dict[str, Any]:
        provider_order = await self.resolve_provider_order(
            credentials,
            strategy_mode=strategy_mode,
            override_provider=override_provider,
        )
        provider_name = provider_order[0]
        provider = self._provider_for(provider_name)
        response = await provider.delete_messages_batch(
            credentials,
            folder=folder,
        )
        self._record_successful_provider(credentials, provider_name)
        return response

    async def send_message(
        self,
        credentials: AccountCredentials,
        *,
        to: str,
        subject: str,
        body_text: str | None = None,
        body_html: str | None = None,
        strategy_mode: str | None = None,
        override_provider: str | None = None,
    ) -> str:
        provider_order = await self.resolve_provider_order(
            credentials,
            strategy_mode=strategy_mode,
            override_provider=override_provider,
        )
        provider_name = provider_order[0]
        provider = self._provider_for(provider_name)
        response = await provider.send_message(
            credentials,
            to=to,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
        )
        self._record_successful_provider(credentials, provider_name)
        return response

    async def resolve_provider_order(
        self,
        credentials: AccountCredentials,
        *,
        strategy_mode: str | None,
        override_provider: str | None,
    ) -> list[str]:
        explicit_provider = self._normalize_provider_name(override_provider)
        if explicit_provider is not None:
            return [explicit_provider]

        strategy = normalize_strategy_mode(strategy_mode or credentials.strategy_mode).value
        if strategy == "graph_only":
            return ["graph_api"]
        if strategy == "imap_only":
            return ["imap"]
        if strategy == "graph_preferred":
            return ["graph_api", "imap"]

        last_provider_used = self._normalize_provider_name(credentials.last_provider_used)
        if last_provider_used is not None:
            return self._with_fallback(last_provider_used)

        stored_provider = self._normalize_provider_name(credentials.api_method)
        if stored_provider is not None:
            return self._with_fallback(stored_provider)

        probe_result = await self._probe_graph_read(credentials)
        if probe_result is not None:
            from graph_api_service import (
                probe_confirms_graph_read_unavailable,
                probe_supports_graph_read,
            )

            if probe_supports_graph_read(probe_result):
                return ["graph_api", "imap"]
            if probe_confirms_graph_read_unavailable(probe_result):
                return ["imap"]

        return ["imap"]

    async def _probe_graph_read(
        self,
        credentials: AccountCredentials,
    ) -> dict[str, Any] | None:
        probe = self.graph_probe
        if probe is None:
            from graph_api_service import check_graph_api_availability

            probe = check_graph_api_availability
        try:
            return await probe(credentials)
        except HTTPException as exc:
            if not self._is_recoverable_graph_probe_http_exception(exc):
                raise
            logger.warning("MailGateway graph probe failed for {}: {}", credentials.email, exc)
            return None
        except RECOVERABLE_GRAPH_PROBE_EXCEPTION_TYPES as exc:
            logger.warning("MailGateway graph probe failed for {}: {}", credentials.email, exc)
            return None

    def _provider_for(self, provider_name: str) -> Any:
        if provider_name == "graph_api":
            return self.graph_provider
        return self.imap_provider

    def _record_successful_provider(
        self,
        credentials: AccountCredentials,
        provider_name: str,
    ) -> None:
        normalized_provider = self._normalize_provider_name(provider_name)
        if normalized_provider is None:
            raise RuntimeError(f"Unsupported provider name: {provider_name}")

        credentials.last_provider_used = normalized_provider
        try:
            persisted = self.persist_provider_hint(credentials.email, normalized_provider)
            if not persisted:
                logger.warning(
                    "MailGateway failed to persist last_provider_used={} for {}",
                    normalized_provider,
                    credentials.email,
                )
        except Exception as exc:
            logger.warning(
                "MailGateway persist last_provider_used failed for {} via {}: {}",
                credentials.email,
                normalized_provider,
                exc,
            )

    def _persist_provider_hint(self, email: str, provider_name: str) -> bool:
        return db.update_account(email, last_provider_used=provider_name)

    def _is_recoverable_http_exception(self, exc: HTTPException) -> bool:
        return exc.status_code in RECOVERABLE_PROVIDER_HTTP_STATUS_CODES

    def _is_recoverable_graph_probe_http_exception(self, exc: HTTPException) -> bool:
        return exc.status_code in RECOVERABLE_GRAPH_PROBE_HTTP_STATUS_CODES

    def _with_fallback(self, primary_provider: str) -> list[str]:
        if primary_provider == "graph_api":
            return ["graph_api", "imap"]
        return ["imap", "graph_api"]

    def _normalize_provider_name(self, provider_name: str | None) -> str | None:
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

    def _model_to_dict(self, model: Any) -> dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump()
        if hasattr(model, "dict"):
            return model.dict()
        if isinstance(model, dict):
            return dict(model)
        return {}

    def _recommended_provider_from_snapshot(self, snapshot_json: str | None) -> str | None:
        if not snapshot_json:
            return None
        try:
            payload = json.loads(snapshot_json)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        return self._normalize_provider_name(payload.get("recommended_provider"))

    def _build_body_preview_from_detail(
        self,
        detail: EmailDetailsResponse,
    ) -> str | None:
        preview_source = detail.body_plain or ""
        if not preview_source and detail.body_html:
            preview_source = re.sub(r"<[^>]+>", " ", detail.body_html)

        compact = " ".join(str(preview_source).split())
        if not compact:
            return None
        return compact[:DETAIL_PREVIEW_MAX_LENGTH]

    async def _hydrate_list_response(
        self,
        provider: Any,
        credentials: AccountCredentials,
        list_response: EmailListResponse,
        *,
        skip_cache: bool,
    ) -> EmailListResponse:
        if not list_response.emails:
            return list_response

        semaphore = asyncio.Semaphore(DETAIL_FETCH_CONCURRENCY_LIMIT)
        target_items = list_response.emails[:DETAIL_HYDRATION_MAX_ITEMS]

        async def fetch_detail(item: Any) -> tuple[str, EmailDetailsResponse | None]:
            try:
                async with semaphore:
                    detail = await provider.get_message_detail(
                        credentials,
                        item.message_id,
                        skip_cache=skip_cache,
                    )
                return item.message_id, detail
            except Exception as exc:  # noqa: BLE001 - 列表增强失败不应打断主列表
                logger.warning(
                    "MailGateway hydrate_details skipped {} for {} via {}: {}",
                    item.message_id,
                    credentials.email,
                    getattr(provider, "name", provider.__class__.__name__),
                    exc,
                )
                return item.message_id, None

        detail_results = await asyncio.gather(
            *(fetch_detail(item) for item in target_items)
        )
        items_by_id = {item.message_id: item for item in list_response.emails}

        for message_id, detail in detail_results:
            if detail is None:
                continue

            item = items_by_id.get(message_id)
            if item is None:
                continue

            if detail.verification_code and not item.verification_code:
                item.verification_code = detail.verification_code
            if detail.to_email and not item.to_email:
                item.to_email = detail.to_email
            if detail.body_plain and not item.body_plain:
                item.body_plain = detail.body_plain
            if detail.body_html and not item.body_html:
                item.body_html = detail.body_html
            if not item.body_preview:
                item.body_preview = self._build_body_preview_from_detail(detail)

        return list_response

    async def _list_messages_with_body_via_provider(
        self,
        provider: Any,
        credentials: AccountCredentials,
        *,
        folder: str,
        page: int,
        page_size: int,
        skip_cache: bool,
        sender_search: str | None,
        subject_search: str | None,
        sort_by: str,
        sort_order: str,
        start_time: str | None,
        end_time: str | None,
    ) -> list[dict[str, Any]]:
        provider_bulk_method = getattr(provider, "list_messages_with_body", None)
        if callable(provider_bulk_method):
            return await provider_bulk_method(
                credentials,
                folder=folder,
                page=page,
                page_size=page_size,
                skip_cache=skip_cache,
                sender_search=sender_search,
                subject_search=subject_search,
                sort_by=sort_by,
                sort_order=sort_order,
                start_time=start_time,
                end_time=end_time,
            )

        list_response = await provider.list_messages(
            credentials,
            folder=folder,
            page=page,
            page_size=page_size,
            skip_cache=skip_cache,
            sender_search=sender_search,
            subject_search=subject_search,
            sort_by=sort_by,
            sort_order=sort_order,
            start_time=start_time,
            end_time=end_time,
        )

        semaphore = asyncio.Semaphore(DETAIL_FETCH_CONCURRENCY_LIMIT)

        async def fetch_detail(item: Any) -> dict[str, Any]:
            async with semaphore:
                detail = await provider.get_message_detail(
                    credentials,
                    item.message_id,
                    skip_cache=skip_cache,
                )
            merged = self._model_to_dict(item)
            merged.update(self._model_to_dict(detail))
            return merged

        return await asyncio.gather(*(fetch_detail(item) for item in list_response.emails))


default_mail_gateway = MailGateway()
