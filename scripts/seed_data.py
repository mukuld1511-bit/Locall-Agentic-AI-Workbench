"""Database Seeding Script for Sovereign Industrial AI Workbench.

Seeds baseline credentials, default roles, policies, knowledge documents,
and sample engineering artifacts for testing and immediate deployment.
All passwords are encrypted with PBKDF2-HMAC-SHA256 (100,000 iterations).
"""

import sys
from pathlib import Path

# Ensure root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database.db import DB
from backend.app.auth.auth_service import AUTH
from backend.app.rbac.rbac_service import RBAC
from backend.app.policy.policy_engine import POLICY
from backend.app.core.config import GLOBAL_CONFIG
from rag.store import KNOWLEDGE_STORE


def seed_database():
    print("[*] Initializing database schema...")
    DB.init_schema()

    print("[*] Seeding default roles and permissions...")
    RBAC.seed_defaults()

    print("[*] Seeding core policies...")
    POLICY.seed_core_policies()

    print("[*] Seeding default industrial users...")
    users = [
        ("admin", "Admin@MRPL2026!", "Chief Security Administrator", "Industrial Cyber-Security", "ADMIN", "secadmin@mrpl.co.in"),
        ("operator_101", "Operator@123!", "Ramesh Kumar", "CDU/VDU Operations", "GRADE_1", "ramesh.k@mrpl.co.in"),
        ("engineer_202", "Engineer@456!", "Priya Sharma", "Mechanical Reliability", "GRADE_2", "priya.s@mrpl.co.in"),
        ("superintendent_303", "Super@789!", "Dr. Arvind Rao", "Technical Services", "GRADE_3", "arvind.r@mrpl.co.in"),
    ]

    for username, password, full_name, dept, role, email in users:
        with DB.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                print(f"  [-] User '{username}' already exists. Skipping.")
                continue

        user = AUTH.create_user(
            username=username,
            password=password,
            full_name=full_name,
            department=dept,
            role=role,
            email=email,
            operator_user_id="SYSTEM_INIT",
        )
        print(f"  [+] Created user: {user['username']} ({user['role']}) - ID: {user['user_id']}")

    # Create sample document files for testing
    docs_dir = GLOBAL_CONFIG.DOCS_STORAGE_DIR
    docs_dir.mkdir(parents=True, exist_ok=True)
    sample_pdf = docs_dir / "scanned_inspection_E1102.pdf"
    if not sample_pdf.exists():
        sample_pdf.write_text("MANGALORE REFINERY AND PETROCHEMICALS LIMITED - Scanned Ultrasonic Thickness Inspection Report for E-1102", encoding="utf-8")

    sample_csv = docs_dir / "unit3_heat_duty_log.csv"
    if not sample_csv.exists():
        sample_csv.write_text("timestamp,temp_in_c,temp_out_c,flow_kg_h,pressure_bar\n08:00,142.5,218.0,45000,21.2\n09:00,143.0,219.2,45200,21.1\n", encoding="utf-8")

    print("[✔] Database seeding complete. Sovereign AI Workbench is ready.")


if __name__ == "__main__":
    seed_database()
