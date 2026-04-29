"""
VerificationRuleDAO - 验证码规则表数据访问对象
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_dao import BaseDAO, get_db_connection


class VerificationRuleDAO(BaseDAO):
    """验证码规则表 DAO"""

    def __init__(self):
        super().__init__("verification_rules")
        self.default_page_size = 100
        self.max_page_size = 1000

    def list_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        conditions: List[str] = []
        params: List[Any] = []
        if enabled_only:
            placeholder = self._get_param_placeholder()
            conditions.append(f"enabled = {placeholder}")
            params.append(True if placeholder == "%s" else 1)

        where_clause = self._build_where_clause(conditions, params)
        order_by = "CASE WHEN scope_type = 'targeted' THEN 0 ELSE 1 END ASC, priority DESC, id ASC"
        rows = self.find_all(where_clause=where_clause, params=params, order_by=order_by)
        rules: List[Dict[str, Any]] = []
        for row in rows:
            rule = self.find_by_id(int(row["id"]))
            if rule:
                rules.append(rule)
        return rules

    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE id = {placeholder}",
                (record_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            rule = self._dict_from_row(row)
            self._ensure_rule_children(cursor, rule)
            conn.commit()
            return self._hydrate_rule(cursor, rule)

    def create_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        matchers = self._normalize_matchers(data.get("matchers"), data)
        extractors = self._normalize_extractors(data.get("extractors"), data)
        payload = self._build_parent_payload(
            data=data,
            matchers=matchers,
            extractors=extractors,
            existing=None,
            is_create=True,
        )

        placeholder = self._get_param_placeholder()
        columns = list(payload.keys())
        values = [payload[column] for column in columns]
        columns_sql = ", ".join(columns)
        placeholders_sql = ", ".join([placeholder] * len(columns))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            if placeholder == "%s":
                cursor.execute(
                    f"INSERT INTO {self.table_name} ({columns_sql}) VALUES ({placeholders_sql}) RETURNING id",
                    values,
                )
                row = cursor.fetchone()
                record_id = int(self._extract_scalar_value(row) or 0)
            else:
                cursor.execute(
                    f"INSERT INTO {self.table_name} ({columns_sql}) VALUES ({placeholders_sql})",
                    values,
                )
                record_id = int(cursor.lastrowid)
            self._replace_rule_children(cursor, record_id, matchers, extractors)
            conn.commit()

        return self.find_by_id(record_id) or {}

    def update_rule(self, rule_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = super().find_by_id(rule_id)
        if not existing:
            return None

        should_sync_children = self._should_sync_children(data)
        matchers = None
        extractors = None
        if should_sync_children:
            matchers = self._normalize_matchers(data.get("matchers"), data, existing)
            extractors = self._normalize_extractors(data.get("extractors"), data, existing)

        payload = self._build_parent_payload(
            data=data,
            matchers=matchers,
            extractors=extractors,
            existing=existing,
            is_create=False,
        )

        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if payload:
                set_clause = ", ".join(f"{column} = {placeholder}" for column in payload.keys())
                values = [payload[column] for column in payload.keys()] + [rule_id]
                cursor.execute(
                    f"UPDATE {self.table_name} SET {set_clause} WHERE id = {placeholder}",
                    values,
                )
                if cursor.rowcount <= 0:
                    conn.rollback()
                    return None
            if should_sync_children and matchers is not None and extractors is not None:
                self._replace_rule_children(cursor, rule_id, matchers, extractors)
            conn.commit()

        return self.find_by_id(rule_id)

    def delete(self, record_id: int) -> bool:
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            self._delete_rule_children(cursor, record_id)
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE id = {placeholder}",
                (record_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _should_sync_children(self, data: Dict[str, Any]) -> bool:
        return any(
            key in data
            for key in (
                "matchers",
                "extractors",
                "sender_pattern",
                "subject_pattern",
                "body_pattern",
                "extract_pattern",
            )
        )

    def _build_parent_payload(
        self,
        *,
        data: Dict[str, Any],
        matchers: Optional[List[Dict[str, Any]]],
        extractors: Optional[List[Dict[str, Any]]],
        existing: Optional[Dict[str, Any]],
        is_create: bool,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}

        if is_create or "name" in data:
            payload["name"] = data.get("name")
        if is_create or "scope_type" in data:
            payload["scope_type"] = data.get("scope_type", existing.get("scope_type") if existing else "global")
        if is_create or "match_mode" in data:
            payload["match_mode"] = data.get("match_mode", existing.get("match_mode") if existing else "and")
        if is_create or "priority" in data:
            payload["priority"] = int(data.get("priority", existing.get("priority") if existing else 0) or 0)
        if is_create or "enabled" in data:
            enabled_value = data.get("enabled", existing.get("enabled") if existing else True)
            payload["enabled"] = bool(enabled_value)
        if is_create or "description" in data:
            payload["description"] = self._clean_optional_text(
                data.get("description", existing.get("description") if existing else None)
            )

        if is_create or self._should_sync_children(data) or "is_regex" in data:
            payload.update(
                self._build_legacy_snapshot(
                    data=data,
                    matchers=matchers,
                    extractors=extractors,
                    existing=existing,
                )
            )

        now = datetime.now().isoformat()
        if is_create:
            payload["created_at"] = now
        payload["updated_at"] = now
        return payload

    def _build_legacy_snapshot(
        self,
        *,
        data: Dict[str, Any],
        matchers: Optional[List[Dict[str, Any]]],
        extractors: Optional[List[Dict[str, Any]]],
        existing: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {}

        if matchers is not None:
            for source_type in ("sender", "subject", "body"):
                first_matcher = next(
                    (item for item in matchers if item["source_type"] == source_type),
                    None,
                )
                snapshot[f"{source_type}_pattern"] = first_matcher["keyword"] if first_matcher else None
        else:
            for source_type in ("sender", "subject", "body"):
                field_name = f"{source_type}_pattern"
                if field_name in data:
                    snapshot[field_name] = self._clean_optional_text(data.get(field_name))
                elif existing is None:
                    snapshot[field_name] = None

        if extractors is not None:
            snapshot["extract_pattern"] = (
                extractors[0]["extract_pattern"] if extractors else ""
            )
        elif "extract_pattern" in data:
            snapshot["extract_pattern"] = self._clean_optional_text(data.get("extract_pattern")) or ""
        elif existing is None:
            snapshot["extract_pattern"] = ""

        if "is_regex" in data:
            snapshot["is_regex"] = bool(data.get("is_regex"))
        elif existing is None or extractors is not None or matchers is not None:
            snapshot["is_regex"] = bool(existing.get("is_regex", True) if existing else True)

        return snapshot

    def _normalize_matchers(
        self,
        raw_matchers: Optional[List[Dict[str, Any]]],
        data: Dict[str, Any],
        existing: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if raw_matchers is None:
            raw_matchers = self._legacy_matchers_from_fields(data, existing)

        normalized: List[Dict[str, Any]] = []
        for index, item in enumerate(raw_matchers, start=1):
            keyword = self._clean_optional_text(item.get("keyword"))
            if not keyword:
                continue
            normalized.append(
                {
                    "source_type": str(item.get("source_type", "body")).lower(),
                    "keyword": keyword,
                    "sort_order": self._normalize_sort_order(item.get("sort_order"), index),
                }
            )
        normalized.sort(key=lambda item: (item["sort_order"], item["source_type"]))
        return normalized

    def _normalize_extractors(
        self,
        raw_extractors: Optional[List[Dict[str, Any]]],
        data: Dict[str, Any],
        existing: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if raw_extractors is None:
            raw_extractors = self._legacy_extractors_from_fields(data, existing)

        normalized: List[Dict[str, Any]] = []
        for index, item in enumerate(raw_extractors, start=1):
            pattern = self._clean_optional_text(item.get("extract_pattern"))
            if not pattern:
                continue
            normalized.append(
                {
                    "source_type": str(item.get("source_type", "body")).lower(),
                    "extract_pattern": pattern,
                    "sort_order": self._normalize_sort_order(item.get("sort_order"), index),
                }
            )
        normalized.sort(key=lambda item: (item["sort_order"], item["source_type"]))
        return normalized

    def _legacy_matchers_from_fields(
        self,
        data: Dict[str, Any],
        existing: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for source_type in ("sender", "subject", "body"):
            field_name = f"{source_type}_pattern"
            value = data.get(field_name) if field_name in data else existing.get(field_name) if existing else None
            keyword = self._clean_optional_text(value)
            if keyword:
                items.append({"source_type": source_type, "keyword": keyword, "sort_order": len(items) + 1})
        return items

    def _legacy_extractors_from_fields(
        self,
        data: Dict[str, Any],
        existing: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        value = data.get("extract_pattern") if "extract_pattern" in data else existing.get("extract_pattern") if existing else None
        pattern = self._clean_optional_text(value)
        if not pattern:
            return []
        return [
            {"source_type": "subject", "extract_pattern": pattern, "sort_order": 1},
            {"source_type": "body", "extract_pattern": pattern, "sort_order": 2},
        ]

    def _ensure_rule_children(self, cursor, rule: Dict[str, Any]) -> None:
        rule_id = int(rule["id"])
        matcher_count = self._count_child_rows(cursor, "verification_rule_matchers", rule_id)
        extractor_count = self._count_child_rows(cursor, "verification_rule_extractors", rule_id)

        if matcher_count == 0:
            legacy_matchers = self._legacy_matchers_from_fields(rule, None)
            if legacy_matchers:
                self._insert_matchers(cursor, rule_id, legacy_matchers)
        if extractor_count == 0:
            legacy_extractors = self._legacy_extractors_from_fields(rule, None)
            if legacy_extractors:
                self._insert_extractors(cursor, rule_id, legacy_extractors)

    def _hydrate_rule(self, cursor, rule: Dict[str, Any]) -> Dict[str, Any]:
        hydrated = dict(rule)
        hydrated["enabled"] = bool(hydrated.get("enabled", True))
        hydrated["is_regex"] = bool(hydrated.get("is_regex", True))
        hydrated["matchers"] = self._fetch_children(
            cursor,
            table_name="verification_rule_matchers",
            rule_id=int(rule["id"]),
        )
        hydrated["extractors"] = self._fetch_children(
            cursor,
            table_name="verification_rule_extractors",
            rule_id=int(rule["id"]),
        )
        return hydrated

    def _replace_rule_children(
        self,
        cursor,
        rule_id: int,
        matchers: List[Dict[str, Any]],
        extractors: List[Dict[str, Any]],
    ) -> None:
        self._delete_rule_children(cursor, rule_id)
        self._insert_matchers(cursor, rule_id, matchers)
        self._insert_extractors(cursor, rule_id, extractors)

    def _delete_rule_children(self, cursor, rule_id: int) -> None:
        placeholder = self._get_param_placeholder()
        cursor.execute(
            f"DELETE FROM verification_rule_matchers WHERE rule_id = {placeholder}",
            (rule_id,),
        )
        cursor.execute(
            f"DELETE FROM verification_rule_extractors WHERE rule_id = {placeholder}",
            (rule_id,),
        )

    def _insert_matchers(self, cursor, rule_id: int, matchers: List[Dict[str, Any]]) -> None:
        self._insert_children(
            cursor,
            table_name="verification_rule_matchers",
            rule_id=rule_id,
            items=matchers,
            value_field="keyword",
        )

    def _insert_extractors(self, cursor, rule_id: int, extractors: List[Dict[str, Any]]) -> None:
        self._insert_children(
            cursor,
            table_name="verification_rule_extractors",
            rule_id=rule_id,
            items=extractors,
            value_field="extract_pattern",
        )

    def _insert_children(
        self,
        cursor,
        *,
        table_name: str,
        rule_id: int,
        items: List[Dict[str, Any]],
        value_field: str,
    ) -> None:
        if not items:
            return

        placeholder = self._get_param_placeholder()
        now = datetime.now().isoformat()
        for index, item in enumerate(items, start=1):
            cursor.execute(
                f"""
                INSERT INTO {table_name} (
                    rule_id,
                    source_type,
                    {value_field},
                    sort_order,
                    created_at,
                    updated_at
                ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (
                    rule_id,
                    item["source_type"],
                    item[value_field],
                    self._normalize_sort_order(item.get("sort_order"), index),
                    now,
                    now,
                ),
            )

    def _fetch_children(self, cursor, *, table_name: str, rule_id: int) -> List[Dict[str, Any]]:
        placeholder = self._get_param_placeholder()
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE rule_id = {placeholder} ORDER BY sort_order ASC, id ASC",
            (rule_id,),
        )
        return self._dicts_from_rows(cursor.fetchall())

    def _count_child_rows(self, cursor, table_name: str, rule_id: int) -> int:
        placeholder = self._get_param_placeholder()
        cursor.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE rule_id = {placeholder}",
            (rule_id,),
        )
        value = self._extract_scalar_value(cursor.fetchone())
        return int(value or 0)

    def _normalize_sort_order(self, value: Any, fallback: int) -> int:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            normalized = fallback
        return normalized if normalized > 0 else fallback

    def _clean_optional_text(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class VerificationDetectionRecordDAO(BaseDAO):
    """验证码识别记录表 DAO"""

    def __init__(self):
        super().__init__("verification_detection_records")
        self.default_page_size = 200
        self.max_page_size = 1000

    def find_existing(
        self,
        email_account: str,
        message_id: str,
        detected_code: str,
        source: str,
    ) -> Optional[Dict[str, Any]]:
        placeholder = self._get_param_placeholder()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM verification_detection_records
                WHERE email_account = {placeholder}
                  AND message_id = {placeholder}
                  AND detected_code = {placeholder}
                  AND source = {placeholder}
                ORDER BY id DESC
                """,
                (email_account, message_id, detected_code, source),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def record_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self.find_existing(
            data["email_account"],
            data["message_id"],
            data["detected_code"],
            data["source"],
        )
        if existing:
            return existing

        payload = data.copy()
        payload["created_at"] = datetime.now().isoformat()
        record_id = self.insert(payload)
        return self.find_by_id(record_id) or {}
