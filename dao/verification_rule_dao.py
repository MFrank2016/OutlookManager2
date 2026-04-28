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
            params.append(True if self._get_param_placeholder() == "%s" else 1)

        where_clause = self._build_where_clause(conditions, params)
        order_by = "CASE WHEN scope_type = 'targeted' THEN 0 ELSE 1 END ASC, priority DESC, id ASC"
        return self.find_all(where_clause=where_clause, params=params, order_by=order_by)

    def create_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = data.copy()
        now = datetime.now().isoformat()
        payload.setdefault("description", None)
        payload["created_at"] = now
        payload["updated_at"] = now
        payload["enabled"] = bool(payload.get("enabled", True))
        record_id = self.insert(payload)
        return self.find_by_id(record_id) or {}

    def update_rule(self, rule_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        payload = data.copy()
        payload["updated_at"] = datetime.now().isoformat()
        if "enabled" in payload:
            payload["enabled"] = bool(payload["enabled"])
        success = self.update(rule_id, payload)
        if not success:
            return None
        return self.find_by_id(rule_id)


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
