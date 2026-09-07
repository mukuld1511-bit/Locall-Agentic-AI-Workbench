"""Centralized Policy Engine for Sovereign Industrial Operations.

Principle:
- DEFAULT = DENY. No action is permitted unless an explicit policy grants it.
- FAIL-CLOSED: Any evaluation failure or ambiguity results in immediate DENY.
- THE LLM IS NEVER THE FINAL SECURITY AUTHORITY.
- Evaluates:
    * User Identity & Role
    * Requested Action & Tool
    * Target Resource & Data Sensitivity
    * Operation Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
    * Air-Gapped Network Constraints
- Returns:
    * ALLOW
    * DENY
    * APPROVAL_REQUIRED
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from backend.app.core.config import GLOBAL_CONFIG
from backend.app.database.db import DB
from backend.app.rbac.rbac_service import RBAC
from backend.app.audit.audit_service import AUDIT


@dataclass
class PolicyEvaluationResult:
    decision: str  # ALLOW, DENY, APPROVAL_REQUIRED
    reason: str
    risk_level: str
    policy_id: Optional[str] = None
    requires_human_approval: bool = False


class PolicyEngine:
    def __init__(self):
        self.db = DB
        self.seed_core_policies()

    def seed_core_policies(self) -> None:
        """Seeds explicit enterprise policies into database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Policy 1: Block all raw database deletion or modification by LLM or standard roles
            cursor.execute(
                """
                INSERT OR IGNORE INTO policies (policy_id, name, role, action, resource, decision, conditions, created_at)
                VALUES ('POL_BLOCK_DB_DELETE', 'Block Database Deletion', '*', 'database_delete', '*', 'DENY', '{"reason": "Direct DB deletion is strictly prohibited"}', datetime('now'))
                """
            )

            # Policy 2: Block external export in air-gapped mode
            cursor.execute(
                """
                INSERT OR IGNORE INTO policies (policy_id, name, role, action, resource, decision, conditions, created_at)
                VALUES ('POL_BLOCK_EXTERNAL_EXPORT', 'Zero-Egress Enforcement', '*', 'external_export', '*', 'DENY', '{"reason": "Air-gapped mode forbids outbound network transmissions"}', datetime('now'))
                """
            )

            # Policy 3: Allow Grade 1 reading public SOPs and chat
            cursor.execute(
                """
                INSERT OR IGNORE INTO policies (policy_id, name, role, action, resource, decision, conditions, created_at)
                VALUES ('POL_GRADE1_READ', 'Grade 1 Operational Reading', 'GRADE_1', 'doc_search', 'classification:PUBLIC_INTERNAL', 'ALLOW', NULL, datetime('now'))
                """
            )

            # Policy 4: Allow Grade 2 and 3 code sandbox execution
            cursor.execute(
                """
                INSERT OR IGNORE INTO policies (policy_id, name, role, action, resource, decision, conditions, created_at)
                VALUES ('POL_SANDBOX_EXEC', 'Sandboxed Code Execution', 'GRADE_2,GRADE_3', 'sandbox_exec', 'sandbox:python', 'ALLOW', '{"max_timeout_sec": 10}', datetime('now'))
                """
            )

            # Policy 5: Equipment parameter override requires approval even for Grade 3
            cursor.execute(
                """
                INSERT OR IGNORE INTO policies (policy_id, name, role, action, resource, decision, conditions, created_at)
                VALUES ('POL_PARAM_OVERRIDE', 'Refinery Parameter Override', 'GRADE_3', 'parameter_override', 'equipment:*', 'APPROVAL_REQUIRED', '{"min_reviewer_role": "ADMIN"}', datetime('now'))
                """
            )
            
            conn.commit()

    def evaluate(
        self,
        user_id: str,
        role: str,
        action: str,
        resource: str,
        tool: Optional[str] = None,
        data_sensitivity: str = "PUBLIC_INTERNAL",
        request_id: Optional[str] = None,
    ) -> PolicyEvaluationResult:
        """Central authorization evaluation. Evaluates Default-Deny, RBAC, and risk level."""
        role_upper = role.upper()

        # Fail-closed guard: unknown role
        if role_upper not in ["GRADE_1", "GRADE_2", "GRADE_3", "ADMIN"]:
            self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "CRITICAL", "Unknown or unauthorized role", request_id)
            return PolicyEvaluationResult("DENY", "Unknown or unauthorized role", "CRITICAL")

        # 1. Absolute Sovereign Prohibition: External Network Egress
        if action in ["external_export", "upload_cloud", "network_send", "curl", "wget"] or tool in ["external_request", "cloud_api"]:
            self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "CRITICAL", "Air-gapped zero-egress violation", request_id)
            return PolicyEvaluationResult("DENY", "Operation denied: Air-gapped zero-egress policy forbids external network egress.", "CRITICAL")

        # 2. Absolute Prohibition: Arbitrary Destructive Host Operations
        if action in ["database_delete", "drop_table", "rm_rf", "system_reboot", "shell_exec_host"]:
            self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "CRITICAL", "Privileged destructive operation prohibited", request_id)
            return PolicyEvaluationResult("DENY", f"Operation '{action}' is strictly prohibited on production infrastructure.", "CRITICAL")

        # 3. Data Sensitivity vs Role Mapping
        # Sensitivity hierarchy: PUBLIC_INTERNAL < ROLE_RESTRICTED < CONFIDENTIAL < HIGHLY_CONFIDENTIAL
        sensitivity_upper = data_sensitivity.upper()
        if sensitivity_upper == "HIGHLY_CONFIDENTIAL":
            if role_upper != "GRADE_3" and role_upper != "ADMIN":
                self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "HIGH", "Insufficient role for HIGHLY_CONFIDENTIAL data", request_id)
                return PolicyEvaluationResult("DENY", "Access Denied: HIGHLY_CONFIDENTIAL materials require Grade 3 clearance.", "HIGH")
            # For Grade 3, accessing highly confidential data requires approval
            if action in ["download", "export_artifact", "parameter_override"]:
                self._log_audit(user_id, role_upper, action, resource, tool, "APPROVAL_REQUIRED", "HIGH", "High-consequence operation on HIGHLY_CONFIDENTIAL resource", request_id)
                return PolicyEvaluationResult("APPROVAL_REQUIRED", "High-consequence operation requires Plant Superintendent approval.", "HIGH", requires_human_approval=True)

        elif sensitivity_upper == "CONFIDENTIAL":
            if role_upper not in ["GRADE_3", "ADMIN"]:
                self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "HIGH", "Insufficient role for CONFIDENTIAL data", request_id)
                return PolicyEvaluationResult("DENY", "Access Denied: CONFIDENTIAL materials require Grade 3 clearance.", "HIGH")

        elif sensitivity_upper == "ROLE_RESTRICTED":
            if role_upper not in ["GRADE_2", "GRADE_3", "ADMIN"]:
                self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "MEDIUM", "Insufficient role for ROLE_RESTRICTED data", request_id)
                return PolicyEvaluationResult("DENY", "Access Denied: ROLE_RESTRICTED documents require Grade 2 or higher clearance.", "MEDIUM")

        # 4. Tool & Action Permission Checks
        if tool == "sandbox_exec":
            if not RBAC.has_permission(role_upper, "CODE_EXECUTE_SANDBOX"):
                self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "MEDIUM", "Role lacks CODE_EXECUTE_SANDBOX permission", request_id)
                return PolicyEvaluationResult("DENY", f"Role '{role_upper}' lacks permission to execute code in sandbox.", "MEDIUM")
            return PolicyEvaluationResult("ALLOW", "Sandboxed execution permitted for role.", "MEDIUM")

        if tool == "doc_generate":
            if not RBAC.has_permission(role_upper, "DOC_GENERATE_OFFICE"):
                self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "MEDIUM", "Role lacks DOC_GENERATE_OFFICE permission", request_id)
                return PolicyEvaluationResult("DENY", f"Role '{role_upper}' cannot generate formal office deliverables.", "MEDIUM")
            return PolicyEvaluationResult("ALLOW", "Deliverable generation permitted.", "MEDIUM")

        if tool == "spreadsheet_read" or tool == "spreadsheet_analyze":
            if not RBAC.has_permission(role_upper, "SPREADSHEET_ANALYZE"):
                self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "MEDIUM", "Role lacks SPREADSHEET_ANALYZE permission", request_id)
                return PolicyEvaluationResult("DENY", f"Role '{role_upper}' cannot analyze spreadsheet records.", "MEDIUM")
            return PolicyEvaluationResult("ALLOW", "Spreadsheet analysis permitted.", "MEDIUM")

        if tool == "vision_analyze" or tool == "ocr":
            # Vision and OCR are allowed for Grade 2 and Grade 3 (and Grade 1 for public inspection reading)
            return PolicyEvaluationResult("ALLOW", "Local multimodal inspection permitted.", "LOW")

        if tool in ["rag_search", "doc_search", "file_read"] or action in ["rag_search", "doc_search", "file_read"]:
            return PolicyEvaluationResult("ALLOW", "Local document query permitted under sensitivity constraints.", "LOW")

        # 5. Standard Chat Interaction
        if action == "chat":
            return PolicyEvaluationResult("ALLOW", "Local chat permitted.", "LOW")

        # 6. Admin Actions
        if action.startswith("admin_"):
            if role_upper != "ADMIN":
                self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "CRITICAL", "Administrative privilege escalation attempt blocked", request_id)
                return PolicyEvaluationResult("DENY", "Access Denied: Administrative operations require ADMIN role.", "CRITICAL")
            return PolicyEvaluationResult("ALLOW", "Administrative operation authorized.", "CRITICAL")

        # 7. DEFAULT DENY
        self._log_audit(user_id, role_upper, action, resource, tool, "DENY", "MEDIUM", "Default-deny triggered (no explicit allow rule)", request_id)
        return PolicyEvaluationResult("DENY", "Operation denied by default: No explicit authorization rule matches request.", "MEDIUM")

    def _log_audit(self, user_id: str, role: str, action: str, resource: str, tool: Optional[str], decision: str, risk: str, reason: str, request_id: Optional[str]) -> None:
        AUDIT.log_event(
            event_type="POLICY_DECISION",
            action=action,
            status="SUCCESS" if decision == "ALLOW" else "BLOCKED",
            user_id=user_id,
            role=role,
            resource=resource,
            tool=tool,
            decision=decision,
            request_id=request_id,
            details={"risk_level": risk, "reason": reason},
        )


POLICY = PolicyEngine()
