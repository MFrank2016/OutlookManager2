"""
验证码规则引擎服务
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional

import database as db
from email_utils import extract_email_address
from logger_config import logger
from verification_code_detector import detect_verification_code


RULE_SCOPE_ORDER = {"targeted": 0, "global": 1}
KEYWORD_HINTS = [
    "verification code",
    "verify code",
    "security code",
    "otp",
    "验证码",
    "驗證碼",
    "安全码",
    "确认码",
    "code",
]


def list_verification_rules(enabled_only: bool = False) -> List[Dict[str, Any]]:
    return db.list_verification_rules(enabled_only)


def create_verification_rule(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = _normalize_rule_payload(data, require_extract_pattern=True)
    return db.create_verification_rule(payload)


def update_verification_rule(rule_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    payload = _normalize_rule_payload(data, require_extract_pattern=True)
    updated = db.update_verification_rule(rule_id, payload)
    if not updated:
        raise ValueError(f"rule {rule_id} not found")
    return updated


def delete_verification_rule(rule_id: int) -> bool:
    return db.delete_verification_rule(rule_id)


def run_verification_rule_test_for_message(
    email_account: str,
    message_id: str,
    rule_id: Optional[int] = None,
) -> Dict[str, Any]:
    email_detail = db.get_cached_email_detail(email_account, message_id)
    if not email_detail:
        raise ValueError(f"未找到测试邮件: {email_account}/{message_id}")

    return detect_verification_code_with_rules(
        email_account=email_account,
        message_id=message_id,
        from_email=email_detail.get("from_email", ""),
        subject=email_detail.get("subject", ""),
        body_plain=email_detail.get("body_plain", ""),
        body_html=email_detail.get("body_html", ""),
        body_preview="",
        source="test",
        page_source="admin-test",
        persist_record=True,
        rule_id=rule_id,
    )


def detect_verification_code_with_rules(
    *,
    email_account: str,
    message_id: str,
    from_email: str = "",
    subject: str = "",
    body_plain: str = "",
    body_html: str = "",
    body_preview: str = "",
    source: str = "runtime",
    page_source: str = "runtime",
    persist_record: bool = True,
    rule_id: Optional[int] = None,
) -> Dict[str, Any]:
    context = _build_email_context(
        from_email=from_email,
        subject=subject,
        body_plain=body_plain,
        body_html=body_html,
        body_preview=body_preview,
    )

    rules = _load_rules(rule_id)
    evaluations: List[Dict[str, Any]] = []

    for rule in rules:
        evaluation = _evaluate_rule(rule, context)
        evaluations.append(evaluation)
        if not evaluation["matched"]:
            continue

        code = _extract_code(rule, context)
        if not code:
            evaluation["matched"] = False
            evaluation["reason"] = "规则命中但未提取到验证码"
            continue

        result = {
            "code": code,
            "matched_rule": rule,
            "matched_via": "rule",
            "source": source,
            "page_source": page_source,
            "rule_evaluations": evaluations,
            "matched_sender": context["from_email"],
            "matched_subject": context["subject"],
            "matched_body_excerpt": _build_excerpt(context["combined_text"], code),
        }
        if persist_record:
            _record_success(email_account, message_id, result)
        return result

    fallback = detect_verification_code("", context["combined_text"])
    if fallback:
        result = {
            "code": _normalize_candidate_code(fallback["code"]),
            "matched_rule": None,
            "matched_via": "fallback",
            "source": source,
            "page_source": page_source,
            "rule_evaluations": evaluations,
            "matched_sender": context["from_email"],
            "matched_subject": context["subject"],
            "matched_body_excerpt": fallback.get("context") or _build_excerpt(context["combined_text"], fallback["code"]),
        }
        if persist_record:
            _record_success(email_account, message_id, result)
        return result

    return {
        "code": None,
        "matched_rule": None,
        "matched_via": None,
        "source": source,
        "page_source": page_source,
        "rule_evaluations": evaluations,
        "matched_sender": context["from_email"],
        "matched_subject": context["subject"],
        "matched_body_excerpt": "",
    }


def _normalize_rule_payload(data: Dict[str, Any], require_extract_pattern: bool) -> Dict[str, Any]:
    payload = {
        "name": (data.get("name") or "").strip(),
        "scope_type": (data.get("scope_type") or "global").strip().lower(),
        "match_mode": (data.get("match_mode") or "and").strip().lower(),
        "priority": int(data.get("priority", 0)),
        "enabled": bool(data.get("enabled", True)),
        "sender_pattern": _clean_optional_text(data.get("sender_pattern")),
        "subject_pattern": _clean_optional_text(data.get("subject_pattern")),
        "body_pattern": _clean_optional_text(data.get("body_pattern")),
        "extract_pattern": _clean_optional_text(data.get("extract_pattern")),
        "is_regex": bool(data.get("is_regex", True)),
        "description": _clean_optional_text(data.get("description")),
    }
    if payload["scope_type"] not in {"targeted", "global"}:
        raise ValueError("scope_type 必须是 targeted 或 global")
    if payload["match_mode"] not in {"and", "or"}:
        raise ValueError("match_mode 必须是 and 或 or")
    if require_extract_pattern and not payload["extract_pattern"]:
        raise ValueError("extract_pattern 不能为空")
    if payload["is_regex"]:
        for field_name in ("sender_pattern", "subject_pattern", "body_pattern", "extract_pattern"):
            pattern = payload.get(field_name)
            if pattern:
                re.compile(pattern, re.IGNORECASE)
    return payload


def _load_rules(rule_id: Optional[int] = None) -> List[Dict[str, Any]]:
    if rule_id is not None:
        rule = db.get_verification_rule(rule_id)
        return [rule] if rule and rule.get("enabled") else []

    rules = list_verification_rules(enabled_only=True)
    rules.sort(
        key=lambda item: (
            RULE_SCOPE_ORDER.get(str(item.get("scope_type", "global")).lower(), 99),
            -int(item.get("priority", 0)),
            int(item.get("id", 0)),
        )
    )
    return rules


def _build_email_context(
    *,
    from_email: str,
    subject: str,
    body_plain: str,
    body_html: str,
    body_preview: str,
) -> Dict[str, str]:
    html_text = _strip_html(body_html)
    combined_text = "\n".join(
        [part for part in [subject, body_preview, body_plain, html_text] if part]
    )
    return {
        "from_email": extract_email_address(from_email) or from_email or "",
        "subject": subject or "",
        "body_plain": body_plain or "",
        "body_html": body_html or "",
        "body_preview": body_preview or "",
        "body_text": "\n".join(
            [part for part in [body_preview, body_plain, html_text] if part]
        ),
        "combined_text": combined_text,
    }


def _evaluate_rule(rule: Dict[str, Any], context: Dict[str, str]) -> Dict[str, Any]:
    checks = {
        "sender": _pattern_match(rule.get("sender_pattern"), context["from_email"], bool(rule.get("is_regex", True))),
        "subject": _pattern_match(rule.get("subject_pattern"), context["subject"], bool(rule.get("is_regex", True))),
        "body": _pattern_match(rule.get("body_pattern"), context["body_text"], bool(rule.get("is_regex", True))),
    }
    active_checks = [value for value in checks.values() if value["configured"]]
    if not active_checks:
        matched = True
        reason = "未配置过滤条件，默认参与提取"
    elif str(rule.get("match_mode", "and")).lower() == "or":
        matched = any(value["matched"] for value in active_checks)
        reason = "OR 命中" if matched else "OR 未命中"
    else:
        matched = all(value["matched"] for value in active_checks)
        reason = "AND 命中" if matched else "AND 未命中"

    return {
        "rule_id": rule.get("id"),
        "rule_name": rule.get("name"),
        "matched": matched,
        "reason": reason,
        "checks": checks,
    }


def _pattern_match(pattern: Optional[str], text: str, is_regex: bool) -> Dict[str, Any]:
    if not pattern:
        return {"configured": False, "matched": False, "pattern": pattern}
    haystack = text or ""
    if is_regex:
        match = re.search(pattern, haystack, re.IGNORECASE)
        return {
            "configured": True,
            "matched": bool(match),
            "pattern": pattern,
        }

    matched = pattern.lower() in haystack.lower()
    return {"configured": True, "matched": matched, "pattern": pattern}


def _extract_code(rule: Dict[str, Any], context: Dict[str, str]) -> Optional[str]:
    pattern = rule.get("extract_pattern") or ""
    if not pattern:
        return None

    search_spaces = [context["subject"], context["body_text"], context["combined_text"]]
    candidates: List[Dict[str, Any]] = []
    for text in search_spaces:
        if not text:
            continue
        for match in re.finditer(pattern, text, re.IGNORECASE):
            candidate = _extract_match_value(match)
            candidate = _normalize_candidate_code(candidate)
            if not candidate:
                continue
            candidates.append(
                {
                    "code": candidate,
                    "score": _score_candidate(text, match.start(), candidate),
                    "position": match.start(),
                }
            )

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item["score"], item["position"]))
    return candidates[0]["code"]


def _extract_match_value(match: re.Match[str]) -> str:
    if match.groups():
        for group in match.groups():
            if group:
                return group
    return match.group(0)


def _score_candidate(text: str, position: int, code: str) -> int:
    lowered = text.lower()
    best_distance = None
    for keyword in KEYWORD_HINTS:
        keyword_pos = lowered.find(keyword.lower())
        if keyword_pos == -1:
            continue
        distance = abs(position - keyword_pos)
        if best_distance is None or distance < best_distance:
            best_distance = distance

    score = 0
    if best_distance is not None:
        score += max(0, 1000 - best_distance)
    if code.isdigit():
        score += 25
    if len(code) == 6:
        score += 10
    return score


def _record_success(email_account: str, message_id: str, result: Dict[str, Any]) -> None:
    matched_rule = result.get("matched_rule") or {}
    payload = {
        "email_account": email_account,
        "message_id": message_id,
        "detected_code": result["code"],
        "rule_id": matched_rule.get("id"),
        "rule_name": matched_rule.get("name"),
        "source": result["source"],
        "page_source": result.get("page_source"),
        "matched_sender": result.get("matched_sender"),
        "matched_subject": result.get("matched_subject"),
        "matched_body_excerpt": result.get("matched_body_excerpt"),
    }
    try:
        db.create_verification_detection_record(payload)
    except Exception as exc:
        logger.warning(f"Failed to record verification detection: {exc}")


def _strip_html(content: str) -> str:
    if not content:
        return ""
    text = re.sub(r"<[^>]+>", " ", content)
    return " ".join(html.unescape(text).split())


def _build_excerpt(text: str, code: str) -> str:
    if not text or not code:
        return ""
    normalized = text.replace("\n", " ")
    position = normalized.lower().find(str(code).lower())
    if position == -1:
        return normalized[:120]
    start = max(0, position - 40)
    end = min(len(normalized), position + len(code) + 40)
    return normalized[start:end].strip()


def _normalize_candidate_code(code: str) -> Optional[str]:
    if not code:
        return None
    normalized = code.strip()
    compact = re.sub(r"[\s-]+", "", normalized)
    if 4 <= len(compact) <= 8 and re.fullmatch(r"[A-Za-z0-9]+", compact):
        return compact.upper() if any(char.isalpha() for char in compact) else compact
    return normalized


def _clean_optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
