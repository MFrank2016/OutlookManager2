"""
验证码规则引擎服务
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional, Tuple

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
MATCHER_SOURCE_TYPES = {"sender", "subject", "body"}
EXTRACTOR_SOURCE_TYPES = {"subject", "body"}


def list_verification_rules(enabled_only: bool = False) -> List[Dict[str, Any]]:
    return db.list_verification_rules(enabled_only)


def create_verification_rule(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = _normalize_rule_payload(data, require_extractors=True)
    return db.create_verification_rule(payload)


def update_verification_rule(rule_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    payload = _normalize_rule_payload(data, require_extractors=True)
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

        code, resolved_code_source, extractor_attempts = _extract_code_from_rule(rule, context)
        evaluation["extractor_attempts"] = extractor_attempts
        if not code:
            evaluation["matched"] = False
            evaluation["reason"] = "规则命中但未提取到验证码"
            continue

        evaluation["reason"] = "规则命中并提取成功"
        result = _build_result(
            code=code,
            matched_rule=rule,
            matched_via="rule",
            source=source,
            page_source=page_source,
            rule_evaluations=evaluations,
            matched_matchers=evaluation["matched_matchers"],
            extractor_attempts=extractor_attempts,
            resolved_code_source=resolved_code_source,
            context=context,
        )
        if persist_record:
            _record_success(email_account, message_id, result)
        return result

    fallback = detect_verification_code("", context["combined_text"])
    debug_evaluation = _latest_debug_evaluation(evaluations)
    if fallback:
        result = _build_result(
            code=_normalize_candidate_code(fallback["code"]),
            matched_rule=None,
            matched_via="fallback",
            source=source,
            page_source=page_source,
            rule_evaluations=evaluations,
            matched_matchers=debug_evaluation.get("matched_matchers", []),
            extractor_attempts=debug_evaluation.get("extractor_attempts", []),
            resolved_code_source=None,
            context=context,
            excerpt_override=fallback.get("context") or _build_excerpt(context["combined_text"], fallback["code"]),
        )
        if persist_record:
            _record_success(email_account, message_id, result)
        return result

    return _build_result(
        code=None,
        matched_rule=None,
        matched_via=None,
        source=source,
        page_source=page_source,
        rule_evaluations=evaluations,
        matched_matchers=debug_evaluation.get("matched_matchers", []),
        extractor_attempts=debug_evaluation.get("extractor_attempts", []),
        resolved_code_source=None,
        context=context,
    )


def _normalize_rule_payload(data: Dict[str, Any], require_extractors: bool) -> Dict[str, Any]:
    payload = {
        "name": (data.get("name") or "").strip(),
        "scope_type": (data.get("scope_type") or "global").strip().lower(),
        "match_mode": (data.get("match_mode") or "or").strip().lower(),
        "priority": int(data.get("priority", 0)),
        "enabled": bool(data.get("enabled", True)),
        "is_regex": bool(data.get("is_regex", True)),
        "description": _clean_optional_text(data.get("description")),
    }
    payload["matchers"] = _normalize_matchers(data)
    payload["extractors"] = _normalize_extractors(data)

    if payload["scope_type"] not in {"targeted", "global"}:
        raise ValueError("scope_type 必须是 targeted 或 global")
    if payload["match_mode"] not in {"and", "or"}:
        raise ValueError("match_mode 必须是 and 或 or")
    if require_extractors and not payload["extractors"]:
        raise ValueError("至少需要 1 条 extractor")

    if payload["is_regex"]:
        for matcher in payload["matchers"]:
            re.compile(matcher["keyword"], re.IGNORECASE)
        for extractor in payload["extractors"]:
            re.compile(extractor["extract_pattern"], re.IGNORECASE)
    return payload


def _normalize_matchers(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_matchers = data.get("matchers")
    if raw_matchers is None:
        raw_matchers = []
        for source_type in ("sender", "subject", "body"):
            keyword = _clean_optional_text(data.get(f"{source_type}_pattern"))
            if keyword:
                raw_matchers.append(
                    {
                        "source_type": source_type,
                        "keyword": keyword,
                        "sort_order": len(raw_matchers) + 1,
                    }
                )

    normalized: List[Dict[str, Any]] = []
    for index, matcher in enumerate(raw_matchers, start=1):
        source_type = str(matcher.get("source_type") or "").strip().lower()
        if source_type not in MATCHER_SOURCE_TYPES:
            raise ValueError("matcher.source_type 必须是 sender / subject / body")
        keyword = _clean_optional_text(matcher.get("keyword"))
        if not keyword:
            raise ValueError("matcher.keyword 不能为空")
        normalized.append(
            {
                "source_type": source_type,
                "keyword": keyword,
                "sort_order": _normalize_sort_order(matcher.get("sort_order"), index),
            }
        )

    normalized.sort(key=lambda item: (item["sort_order"], item["source_type"]))
    return normalized


def _normalize_extractors(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_extractors = data.get("extractors")
    if raw_extractors is None:
        pattern = _clean_optional_text(data.get("extract_pattern"))
        raw_extractors = []
        if pattern:
            raw_extractors = [
                {"source_type": "subject", "extract_pattern": pattern, "sort_order": 1},
                {"source_type": "body", "extract_pattern": pattern, "sort_order": 2},
            ]

    normalized: List[Dict[str, Any]] = []
    for index, extractor in enumerate(raw_extractors, start=1):
        source_type = str(extractor.get("source_type") or "").strip().lower()
        if source_type not in EXTRACTOR_SOURCE_TYPES:
            raise ValueError("extractor.source_type 必须是 subject / body")
        extract_pattern = _clean_optional_text(extractor.get("extract_pattern"))
        if not extract_pattern:
            raise ValueError("extractor.extract_pattern 不能为空")
        normalized.append(
            {
                "source_type": source_type,
                "extract_pattern": extract_pattern,
                "sort_order": _normalize_sort_order(extractor.get("sort_order"), index),
            }
        )

    normalized.sort(key=lambda item: (item["sort_order"], item["source_type"]))
    return normalized


def _normalize_sort_order(value: Any, fallback: int) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = fallback
    return normalized if normalized > 0 else fallback


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
    matchers = sorted(
        rule.get("matchers", []),
        key=lambda item: (int(item.get("sort_order", 0)), int(item.get("id", 0))),
    )
    if not matchers:
        return {
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "matched": True,
            "reason": "未配置 matcher，默认进入提取阶段",
            "matcher_results": [],
            "matched_matchers": [],
            "extractor_attempts": [],
        }

    matcher_results: List[Dict[str, Any]] = []
    matched_matchers: List[Dict[str, Any]] = []
    for matcher in matchers:
        source_text = _resolve_context_value(context, str(matcher.get("source_type", "body")))
        outcome = _keyword_match(
            pattern=str(matcher.get("keyword", "")),
            text=source_text,
            is_regex=bool(rule.get("is_regex", True)),
        )
        matcher_result = {
            "id": matcher.get("id"),
            "source_type": matcher.get("source_type"),
            "keyword": matcher.get("keyword"),
            "sort_order": matcher.get("sort_order"),
            "matched": outcome["matched"],
            "configured": True,
        }
        matcher_results.append(matcher_result)
        if outcome["matched"]:
            matched_matchers.append(
                {
                    "id": matcher.get("id"),
                    "source_type": matcher.get("source_type"),
                    "keyword": matcher.get("keyword"),
                    "sort_order": matcher.get("sort_order"),
                }
            )

    matched = bool(matched_matchers)
    return {
        "rule_id": rule.get("id"),
        "rule_name": rule.get("name"),
        "matched": matched,
        "reason": "任意 matcher 命中" if matched else "未命中任何 matcher",
        "matcher_results": matcher_results,
        "matched_matchers": matched_matchers,
        "extractor_attempts": [],
    }


def _keyword_match(pattern: str, text: str, is_regex: bool) -> Dict[str, Any]:
    haystack = text or ""
    if is_regex:
        match = re.search(pattern, haystack, re.IGNORECASE)
        return {"matched": bool(match), "pattern": pattern}
    return {"matched": pattern.lower() in haystack.lower(), "pattern": pattern}


def _extract_code_from_rule(
    rule: Dict[str, Any],
    context: Dict[str, str],
) -> Tuple[Optional[str], Optional[str], List[Dict[str, Any]]]:
    extractors = sorted(
        rule.get("extractors", []),
        key=lambda item: (int(item.get("sort_order", 0)), int(item.get("id", 0))),
    )
    attempts: List[Dict[str, Any]] = []
    for extractor in extractors:
        source_type = str(extractor.get("source_type", "body"))
        source_text = _resolve_context_value(context, source_type)
        code = _extract_from_text(
            pattern=str(extractor.get("extract_pattern", "")),
            text=source_text,
            is_regex=bool(rule.get("is_regex", True)),
        )
        attempts.append(
            {
                "id": extractor.get("id"),
                "source_type": source_type,
                "extract_pattern": extractor.get("extract_pattern"),
                "sort_order": extractor.get("sort_order"),
                "matched": bool(code),
                "code": code,
            }
        )
        if code:
            return code, source_type, attempts
    return None, None, attempts


def _extract_from_text(pattern: str, text: str, is_regex: bool) -> Optional[str]:
    if not pattern or not text:
        return None

    if not is_regex:
        position = text.lower().find(pattern.lower())
        if position == -1:
            return None
        return _normalize_candidate_code(text[position : position + len(pattern)])

    candidates: List[Dict[str, Any]] = []
    for match in re.finditer(pattern, text, re.IGNORECASE):
        candidate = _normalize_candidate_code(_extract_match_value(match))
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


def _build_result(
    *,
    code: Optional[str],
    matched_rule: Optional[Dict[str, Any]],
    matched_via: Optional[str],
    source: str,
    page_source: str,
    rule_evaluations: List[Dict[str, Any]],
    matched_matchers: List[Dict[str, Any]],
    extractor_attempts: List[Dict[str, Any]],
    resolved_code_source: Optional[str],
    context: Dict[str, str],
    excerpt_override: Optional[str] = None,
) -> Dict[str, Any]:
    excerpt = excerpt_override
    if excerpt is None:
        excerpt = _build_excerpt(
            _resolve_context_value(context, resolved_code_source or "body"),
            code or "",
        )
        if not excerpt:
            excerpt = _build_excerpt(context["combined_text"], code or "")

    return {
        "code": code,
        "matched_rule": matched_rule,
        "matched_via": matched_via,
        "source": source,
        "page_source": page_source,
        "rule_evaluations": rule_evaluations,
        "matched_matchers": matched_matchers,
        "extractor_attempts": extractor_attempts,
        "resolved_code_source": resolved_code_source,
        "matched_sender": context["from_email"],
        "matched_subject": context["subject"],
        "matched_body_excerpt": excerpt,
    }


def _latest_debug_evaluation(evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    for evaluation in reversed(evaluations):
        if evaluation.get("matched_matchers") or evaluation.get("extractor_attempts"):
            return evaluation
    return evaluations[-1] if evaluations else {}


def _resolve_context_value(context: Dict[str, str], source_type: str) -> str:
    if source_type == "sender":
        return context["from_email"]
    if source_type == "subject":
        return context["subject"]
    return context["body_text"]


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
