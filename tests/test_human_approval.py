"""Tests for Human-in-the-Loop Approval Workflow.

Validates the complete lifecycle:
1. User proposes a high-risk operation (e.g., equipment parameter override).
2. Policy Engine returns APPROVAL_REQUIRED.
3. Approval request is persisted in the approvals table.
4. Admin/Superintendent reviews and approves or rejects.
5. Audit trail captures every transition.
"""

import unittest
from backend.app.database.db import DB
from backend.app.auth.auth_service import AUTH
from backend.app.policy.policy_engine import POLICY
from backend.app.audit.audit_service import AUDIT


class TestHumanApprovalWorkflow(unittest.TestCase):
    def setUp(self):
        DB.init_schema()

    def test_high_risk_action_triggers_approval_required(self):
        """Grade 3 attempting equipment parameter override should trigger APPROVAL_REQUIRED."""
        result = POLICY.evaluate(
            user_id="usr_super303",
            role="GRADE_3",
            action="parameter_override",
            resource="equipment:E-1102",
            data_sensitivity="HIGHLY_CONFIDENTIAL",
        )
        self.assertEqual(result.decision, "APPROVAL_REQUIRED")
        self.assertTrue(result.requires_human_approval)

    def test_create_approval_request(self):
        """Creating an approval request should persist in the database."""
        approval_id = POLICY.create_approval_request(
            request_id="req_test_001",
            user_id="usr_eng202",
            action="parameter_override",
            resource="equipment:E-1102",
            reason="Override operating pressure setpoint for turnaround maintenance.",
        )
        self.assertTrue(approval_id.startswith("appr_"))

        # Verify persistence
        pending = POLICY.get_pending_approvals()
        found = any(a["approval_id"] == approval_id for a in pending)
        self.assertTrue(found)

    def test_admin_approves_request(self):
        """Admin can approve a pending approval request."""
        approval_id = POLICY.create_approval_request(
            request_id="req_test_approve",
            user_id="usr_eng202",
            action="parameter_override",
            resource="equipment:P-4401",
            reason="Recalibrate relief valve pressure setpoint.",
        )

        result = POLICY.review_approval(
            approval_id=approval_id,
            reviewer_id="usr_admin",
            reviewer_role="ADMIN",
            decision="APPROVE",
            comment="Approved for turnaround maintenance window.",
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "APPROVED")

    def test_admin_rejects_request(self):
        """Admin can reject a pending approval request."""
        approval_id = POLICY.create_approval_request(
            request_id="req_test_reject",
            user_id="usr_eng202",
            action="parameter_override",
            resource="equipment:V-5501",
            reason="Reduce minimum wall thickness threshold.",
        )

        result = POLICY.review_approval(
            approval_id=approval_id,
            reviewer_id="usr_admin",
            reviewer_role="ADMIN",
            decision="REJECT",
            comment="Rejected: Insufficient engineering justification provided.",
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "REJECTED")

    def test_grade_1_cannot_review_approvals(self):
        """Grade 1 operator should not be able to review approval requests."""
        approval_id = POLICY.create_approval_request(
            request_id="req_test_unauth",
            user_id="usr_eng202",
            action="parameter_override",
            resource="equipment:E-1102",
            reason="Test unauthorized review.",
        )

        result = POLICY.review_approval(
            approval_id=approval_id,
            reviewer_id="usr_op101",
            reviewer_role="GRADE_1",
            decision="APPROVE",
        )
        self.assertFalse(result["success"])
        self.assertIn("Insufficient privileges", result["error"])

    def test_cannot_double_approve(self):
        """Already finalized approval should not be modifiable."""
        approval_id = POLICY.create_approval_request(
            request_id="req_test_double",
            user_id="usr_eng202",
            action="parameter_override",
            resource="equipment:E-1102",
            reason="Double approval test.",
        )

        # First approval
        POLICY.review_approval(approval_id, "usr_admin", "ADMIN", "APPROVE")

        # Attempt second approval
        result = POLICY.review_approval(approval_id, "usr_admin", "ADMIN", "REJECT")
        self.assertFalse(result["success"])
        self.assertIn("already finalized", result["error"])

    def test_approval_lookup_by_request_id(self):
        """Should be able to find approval by its original request_id."""
        req_id = "req_lookup_test_001"
        POLICY.create_approval_request(
            request_id=req_id,
            user_id="usr_eng202",
            action="parameter_override",
            resource="equipment:E-1102",
            reason="Lookup test.",
        )

        found = POLICY.get_approval_by_request_id(req_id)
        self.assertIsNotNone(found)
        self.assertEqual(found["request_id"], req_id)
        self.assertEqual(found["status"], "PENDING")

    def test_approval_creates_audit_trail(self):
        """Each approval action should generate audit events."""
        initial_events = AUDIT.get_recent_events(limit=100)
        initial_count = len(initial_events)

        approval_id = POLICY.create_approval_request(
            request_id="req_audit_trail",
            user_id="usr_eng202",
            action="parameter_override",
            resource="equipment:E-1102",
            reason="Audit trail verification test.",
        )
        POLICY.review_approval(approval_id, "usr_admin", "ADMIN", "APPROVE")

        final_events = AUDIT.get_recent_events(limit=100)
        # Should have at least 2 new events: APPROVAL_REQUESTED + APPROVAL_APPROVED
        self.assertGreater(len(final_events), initial_count)

        # Check for approval-related event types
        event_types = [e["event_type"] for e in final_events]
        self.assertIn("APPROVAL_REQUESTED", event_types)
        self.assertIn("APPROVAL_APPROVED", event_types)


if __name__ == "__main__":
    unittest.main()
