import asyncio
from datetime import datetime

import admin_api
import database as db


def _clear_rule_tables() -> None:
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        for table_name in (
            "verification_detection_records",
            "verification_rule_matchers",
            "verification_rule_extractors",
            "verification_rules",
        ):
            cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()


def setup_function():
    _clear_rule_tables()


def teardown_function():
    _clear_rule_tables()


def _admin():
    return {"role": "admin", "username": "tester", "is_active": True}


def _matcher(source_type: str, keyword: str, sort_order: int):
    return admin_api.VerificationRuleMatcherInput(
        source_type=source_type,
        keyword=keyword,
        sort_order=sort_order,
    )


def _extractor(source_type: str, pattern: str, sort_order: int):
    return admin_api.VerificationRuleExtractorInput(
        source_type=source_type,
        extract_pattern=pattern,
        sort_order=sort_order,
    )


def test_admin_rule_crud_and_test_endpoint():
    async def _run():
        created = await admin_api.create_verification_rule_route(
            admin_api.VerificationRuleUpsertRequest(
                name="Admin 规则",
                scope_type="global",
                match_mode="or",
                priority=10,
                enabled=True,
                matchers=[
                    _matcher("sender", "github", 1),
                    _matcher("subject", "verification", 2),
                ],
                extractors=[
                    _extractor("subject", r"(\d{6})", 1),
                    _extractor("body", r"(\d{6})", 2),
                ],
                description="admin route create",
            ),
            admin=_admin(),
        )

        assert len(created.matchers) == 2
        assert created.extractors[1].source_type == "body"

        listing = await admin_api.list_verification_rules_route(admin=_admin())
        assert listing.total == 1
        assert listing.rules[0].id == created.id
        assert listing.rules[0].matchers[0].source_type == "sender"

        updated = await admin_api.update_verification_rule_route(
            created.id,
            admin_api.VerificationRuleUpsertRequest(
                name="Admin 规则 v2",
                scope_type="targeted",
                match_mode="or",
                priority=20,
                enabled=True,
                matchers=[
                    _matcher("sender", "github", 1),
                    _matcher("body", "otp", 2),
                ],
                extractors=[
                    _extractor("subject", r"(\d{6})", 1),
                    _extractor("body", r"(\d{6})", 2),
                ],
                description="updated",
            ),
            admin=_admin(),
        )
        assert updated.scope_type == "targeted"
        assert updated.priority == 20
        assert updated.matchers[1].source_type == "body"

        db.cache_email_detail(
            "demo@example.com",
            {
                "message_id": "demo-msg",
                "subject": "GitHub verification",
                "from_email": "noreply@github.com",
                "to_email": "demo@example.com",
                "date": datetime.now().isoformat(),
                "body_plain": "Your OTP is 123456",
                "body_html": None,
                "verification_code": None,
            },
        )

        test_result = await admin_api.test_verification_rule_route(
            admin_api.VerificationRuleTestRequest(
                email_account="demo@example.com",
                message_id="demo-msg",
                rule_id=created.id,
            ),
            admin=_admin(),
        )
        assert test_result.code == "123456"
        assert test_result.matched_rule is not None
        assert test_result.matched_rule["name"] == "Admin 规则 v2"
        assert [item["source_type"] for item in test_result.matched_matchers] == ["sender", "body"]
        assert [item["source_type"] for item in test_result.extractor_attempts] == ["subject", "body"]
        assert test_result.resolved_code_source == "body"

        deleted = await admin_api.delete_verification_rule_route(created.id, admin=_admin())
        assert "删除成功" in deleted.message

    asyncio.run(_run())


def test_admin_test_endpoint_uses_supplied_message_id():
    async def _run():
        created = await admin_api.create_verification_rule_route(
            admin_api.VerificationRuleUpsertRequest(
                name="Message ID 规则",
                scope_type="global",
                match_mode="or",
                priority=5,
                enabled=True,
                matchers=[_matcher("sender", "contoso", 1)],
                extractors=[_extractor("body", r"(\d{6})", 1)],
            ),
            admin=_admin(),
        )

        db.cache_email_detail(
            "picker@example.com",
            {
                "message_id": "msg-1",
                "subject": "Ignore me",
                "from_email": "login@contoso.com",
                "to_email": "picker@example.com",
                "date": datetime.now().isoformat(),
                "body_plain": "Old code 111111",
                "body_html": None,
                "verification_code": None,
            },
        )
        db.cache_email_detail(
            "picker@example.com",
            {
                "message_id": "msg-2",
                "subject": "Use this one",
                "from_email": "login@contoso.com",
                "to_email": "picker@example.com",
                "date": datetime.now().isoformat(),
                "body_plain": "New code 222222",
                "body_html": None,
                "verification_code": None,
            },
        )

        result = await admin_api.test_verification_rule_route(
            admin_api.VerificationRuleTestRequest(
                email_account="picker@example.com",
                message_id="msg-2",
                rule_id=created.id,
            ),
            admin=_admin(),
        )

        assert result.code == "222222"
        assert result.matched_rule is not None
        assert result.matched_rule["id"] == created.id

    asyncio.run(_run())
