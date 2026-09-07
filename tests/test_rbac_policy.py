"""Security Tests for RBAC, Default-Deny, and Policy Engine Boundaries."""

import unittest
from backend.app.database.db import DB
from backend.app.policy.policy_engine import POLICY
from backend.app.rbac.rbac_service import RBAC


class TestRBACAndPolicyEngine(unittest.TestCase):
    def setUp(self):
        DB.init_schema()

    def test_default_deny_unmapped_action(self):
        # An unmapped random action must be DENIED by default
        result = POLICY.evaluate(
            user_id="usr_test",
            role="GRADE_1",
            action="unknown_custom_action_xyz",
            resource="server:port",
        )
        self.assertEqual(result.decision, "DENY")
        self.assertIn("default", result.reason.lower())

    def test_grade_1_cannot_execute_sandbox_code(self):
        # Grade 1 operator attempts to invoke Python sandbox
        result = POLICY.evaluate(
            user_id="usr_op101",
            role="GRADE_1",
            action="sandbox_exec",
            resource="sandbox:python",
            tool="sandbox_exec",
        )
        self.assertEqual(result.decision, "DENY")
        self.assertIn("lacks permission", result.reason.lower())

    def test_grade_2_can_execute_sandbox_code(self):
        # Grade 2 reliability engineer can invoke Python sandbox
        result = POLICY.evaluate(
            user_id="usr_eng202",
            role="GRADE_2",
            action="sandbox_exec",
            resource="sandbox:python",
            tool="sandbox_exec",
        )
        self.assertEqual(result.decision, "ALLOW")

    def test_database_delete_is_strictly_blocked_for_all(self):
        # Destructive database deletion is blocked even if requested
        for role in ["GRADE_1", "GRADE_2", "GRADE_3", "ADMIN"]:
            result = POLICY.evaluate(
                user_id="usr_any",
                role=role,
                action="database_delete",
                resource="production_db",
            )
            self.assertEqual(result.decision, "DENY")

    def test_external_export_is_blocked_zero_egress(self):
        # Outbound network transmissions are blocked in air-gapped mode
        result = POLICY.evaluate(
            user_id="usr_super",
            role="GRADE_3",
            action="external_export",
            resource="cloud:storage",
            tool="external_request",
        )
        self.assertEqual(result.decision, "DENY")
        self.assertIn("air-gapped", result.reason.lower())

    def test_confidential_document_access_control(self):
        # Grade 1 denied CONFIDENTIAL data
        res1 = POLICY.evaluate(
            user_id="usr_op",
            role="GRADE_1",
            action="doc_search",
            resource="doc:pid_matrix",
            data_sensitivity="CONFIDENTIAL",
        )
        self.assertEqual(res1.decision, "DENY")

        # Grade 3 permitted CONFIDENTIAL data
        res3 = POLICY.evaluate(
            user_id="usr_super",
            role="GRADE_3",
            action="doc_search",
            resource="doc:pid_matrix",
            data_sensitivity="CONFIDENTIAL",
        )
        self.assertEqual(res3.decision, "ALLOW")


if __name__ == "__main__":
    unittest.main()
