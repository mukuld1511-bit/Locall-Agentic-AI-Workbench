"""End-to-End Workflow Integration and Security Validation Tests."""

import unittest
from backend.app.database.db import DB
from backend.app.auth.auth_service import AUTH
from backend.app.workflows.workflow_engine import WORKFLOW_ENGINE
from backend.app.audit.audit_service import AUDIT
from backend.app.policy.policy_engine import POLICY


class TestE2EWorkflows(unittest.TestCase):
    def setUp(self):
        DB.init_schema()

    def test_inspection_audit_workflow_e2e(self):
        # Retrieve actual user_id for engineer_202
        with DB.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = 'engineer_202'")
            row = cursor.fetchone()
            user_id = row["user_id"] if row else "usr_eng202"

        # Grade 2 Engineer requests heat exchanger inspection audit
        task = "Audit scanned ultrasonic thickness inspection report for crude preheat heat exchanger E-1102 and generate official approval note."
        state = WORKFLOW_ENGINE.execute_workflow(
            task_description=task,
            user_id=user_id,
            role="GRADE_2",
            session_id="sess_test_123",
        )

        self.assertEqual(state.status, "COMPLETED")
        self.assertGreater(len(state.completed_steps), 0)
        self.assertEqual(len(state.failed_steps), 0)
        self.assertGreater(len(state.generated_artifacts), 0)
        self.assertEqual(state.verification_summary["overall_status"], "PASS")
        self.assertIn("Approval Note", state.final_response)

    def test_grade_1_database_delete_security_block(self):
        # Grade 1 operator attempts to delete production database
        policy_eval = POLICY.evaluate(
            user_id="usr_op101",
            role="GRADE_1",
            action="database_delete",
            resource="production_db",
        )
        self.assertEqual(policy_eval.decision, "DENY")
        self.assertIn("prohibited", policy_eval.reason.lower())

    def test_audit_integrity_verification(self):
        # Audit log hash-chain must verify 100% valid
        integrity = AUDIT.verify_integrity()
        self.assertTrue(integrity["verified"])
        self.assertTrue(integrity["chain_valid"])
        self.assertGreater(integrity["total_records_checked"], 0)


if __name__ == "__main__":
    unittest.main()
