"""Role-Based Access Control (RBAC) Service for Sovereign Industrial Operations.

Enforces server-side authorization mapped to configurable enterprise roles:
- GRADE_1: Plant Operator / Junior Technician (Low-risk search, summarization, read-only)
- GRADE_2: Process & Maintenance Engineer (Medium-risk, Python sandbox, spreadsheets, reporting)
- GRADE_3: Plant Superintendent / Chief Technical Officer (High-risk operations, confidential documents)
- ADMIN: Industrial Systems & Security Administrator (Policy, user, model, and audit governance)
"""

from typing import Dict, List, Set
from backend.app.database.db import DB


# Canonical Permissions
PERMISSIONS_CATALOGUE = [
    # Low-Risk Permissions
    {"id": "CHAT_INTERACT", "name": "Basic AI Chat Interaction", "risk": "LOW", "desc": "Chat with Organizer and General worker"},
    {"id": "DOC_SEARCH_PUBLIC", "name": "Search Public Documents", "risk": "LOW", "desc": "Access and query public refinery SOPs"},
    {"id": "DOC_SUMMARIZE", "name": "Document Summarization", "risk": "LOW", "desc": "Summarize standard operational records"},
    {"id": "REPORT_READ", "name": "Read Operational Reports", "risk": "LOW", "desc": "View generated operational reports"},
    
    # Medium-Risk Permissions
    {"id": "CODE_EXECUTE_SANDBOX", "name": "Execute Code in Sandbox", "risk": "MEDIUM", "desc": "Run calculations in isolated local sandbox"},
    {"id": "SPREADSHEET_ANALYZE", "name": "Spreadsheet Processing", "risk": "MEDIUM", "desc": "Process and analyze equipment efficiency sheets"},
    {"id": "DOC_GENERATE_OFFICE", "name": "Generate Word/Excel/PPT Deliverables", "risk": "MEDIUM", "desc": "Produce operational notes and summaries"},
    {"id": "VISION_PID_ANALYZE", "name": "P&ID & Diagram Inspection", "risk": "MEDIUM", "desc": "Inspect piping and instrumentation diagrams"},
    {"id": "DOC_SEARCH_RESTRICTED", "name": "Search Restricted SOPs", "risk": "MEDIUM", "desc": "Access department-restricted operational docs"},
    
    # High-Risk Permissions
    {"id": "PRIVILEGED_WORKFLOW", "name": "Execute High-Consequence Workflows", "risk": "HIGH", "desc": "Run refinery shutdown or overhaul analysis"},
    {"id": "DOC_SEARCH_CONFIDENTIAL", "name": "Access Confidential Blueprints", "risk": "HIGH", "desc": "Read proprietary process chemistry manuals"},
    {"id": "EQUIPMENT_OVERRIDE_SIM", "name": "Simulate Parameter Overrides", "risk": "HIGH", "desc": "Run engineering parameter simulations"},
    
    # Critical / Admin Permissions
    {"id": "ADMIN_USER_MANAGE", "name": "User Account Management", "risk": "CRITICAL", "desc": "Create, lock, or modify user accounts"},
    {"id": "ADMIN_POLICY_MANAGE", "name": "Policy Engine Administration", "risk": "CRITICAL", "desc": "Update authorization and default-deny policies"},
    {"id": "ADMIN_MODEL_MANAGE", "name": "Model Registry Administration", "risk": "CRITICAL", "desc": "Register, swap, and configure open-weight LLMs"},
    {"id": "ADMIN_AUDIT_INSPECT", "name": "Audit Trail Inspection", "risk": "CRITICAL", "desc": "Inspect and verify tamper-evident audit chains"},
]

DEFAULT_ROLE_MAPPINGS: Dict[str, List[str]] = {
    "GRADE_1": [
        "CHAT_INTERACT",
        "DOC_SEARCH_PUBLIC",
        "DOC_SUMMARIZE",
        "REPORT_READ",
    ],
    "GRADE_2": [
        "CHAT_INTERACT",
        "DOC_SEARCH_PUBLIC",
        "DOC_SUMMARIZE",
        "REPORT_READ",
        "CODE_EXECUTE_SANDBOX",
        "SPREADSHEET_ANALYZE",
        "DOC_GENERATE_OFFICE",
        "VISION_PID_ANALYZE",
        "DOC_SEARCH_RESTRICTED",
    ],
    "GRADE_3": [
        "CHAT_INTERACT",
        "DOC_SEARCH_PUBLIC",
        "DOC_SUMMARIZE",
        "REPORT_READ",
        "CODE_EXECUTE_SANDBOX",
        "SPREADSHEET_ANALYZE",
        "DOC_GENERATE_OFFICE",
        "VISION_PID_ANALYZE",
        "DOC_SEARCH_RESTRICTED",
        "PRIVILEGED_WORKFLOW",
        "DOC_SEARCH_CONFIDENTIAL",
        "EQUIPMENT_OVERRIDE_SIM",
    ],
    "ADMIN": [
        "CHAT_INTERACT",
        "DOC_SEARCH_PUBLIC",
        "DOC_SUMMARIZE",
        "REPORT_READ",
        "ADMIN_USER_MANAGE",
        "ADMIN_POLICY_MANAGE",
        "ADMIN_MODEL_MANAGE",
        "ADMIN_AUDIT_INSPECT",
    ],
}


class RBACService:
    def __init__(self):
        self.db = DB
        self.seed_defaults()

    def seed_defaults(self) -> None:
        """Seeds default permissions and role bindings into database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert permissions
            for p in PERMISSIONS_CATALOGUE:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO permissions (permission_id, name, description, risk_level)
                    VALUES (?, ?, ?, ?)
                    """,
                    (p["id"], p["name"], p["desc"], p["risk"]),
                )

            # Insert role mappings
            for role, perm_ids in DEFAULT_ROLE_MAPPINGS.items():
                for pid in perm_ids:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO role_permissions (role, permission_id)
                        VALUES (?, ?)
                        """,
                        (role, pid),
                    )
            conn.commit()

    def get_role_permissions(self, role: str) -> Set[str]:
        """Returns set of permission IDs assigned to a role."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT permission_id FROM role_permissions WHERE role = ?", (role.upper(),))
            rows = cursor.fetchall()
            return {row["permission_id"] for row in rows}

    def has_permission(self, role: str, permission_id: str) -> bool:
        """Checks if a role possesses the specified permission."""
        perms = self.get_role_permissions(role)
        return permission_id in perms

    def list_all_roles(self) -> Dict[str, List[str]]:
        """Returns all configured roles and their permissions."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, permission_id FROM role_permissions ORDER BY role, permission_id")
            rows = cursor.fetchall()
            result: Dict[str, List[str]] = {}
            for row in rows:
                result.setdefault(row["role"], []).append(row["permission_id"])
            return result


RBAC = RBACService()
