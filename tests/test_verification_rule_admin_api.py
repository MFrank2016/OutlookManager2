import asyncio
from datetime import datetime

import admin_api
import database as db


def _clear_rule_tables() -> None:
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM verification_detection_records")
        cursor.execute("DELETE FROM verification_rules")
        conn.commit()


def setup_function():
    _clear_rule_tables()


def teardown_function():
    _clear_rule_tables()


def _admin():
    return {"role": "admin", "username": "tester", "is_active": True}


def test_admin_rule_crud_and_test_endpoint():
    async def _run():
        created = await admin_api.create_verification_rule_route(
            admin_api.VerificationRuleUpsertRequest(
                name="Admin 规则",
                scope_type="global",
                match_mode="and",
                priority=10,
                enabled=True,
                body_pattern="security code",
                extract_pattern=r"(\d{6})",
                is_regex=True,
                description="admin route create",
            ),
            admin=_admin(),
        )

        listing = await admin_api.list_verification_rules_route(admin=_admin())
        assert listing.total == 1
        assert listing.rules[0].id == created.id

        updated = await admin_api.update_verification_rule_route(
            created.id,
            admin_api.VerificationRuleUpsertRequest(
                name="Admin 规则 v2",
                scope_type="targeted",
                match_mode="or",
                priority=20,
                enabled=True,
                sender_pattern="github",
                body_pattern="otp",
                extract_pattern=r"(\d{6})",
                is_regex=True,
                description="updated",
            ),
            admin=_admin(),
        )
        assert updated.scope_type == "targeted"
        assert updated.priority == 20

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

        deleted = await admin_api.delete_verification_rule_route(created.id, admin=_admin())
        assert "删除成功" in deleted.message

    asyncio.run(_run())
