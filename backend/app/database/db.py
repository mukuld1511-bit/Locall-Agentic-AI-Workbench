"""Local SQLite Database Manager for Sovereign Industrial AI Workbench.

Implements zero-cloud persistent storage for:
- Users, credentials (hashed), and account states
- Active sessions and expiration tokens
- RBAC roles and granular permissions
- Centralized policy definitions
- Document catalogue and access classification
- Audit trail events (tamper-evident SHA-256 hash chaining)
- Model registry records and resource metrics
- Human-in-the-loop approval requests
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import GLOBAL_CONFIG


class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or GLOBAL_CONFIG.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_schema(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Users Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                department TEXT NOT NULL,
                role TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, LOCKED, DISABLED
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)

            # 2. Sessions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                last_activity TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
            """)

            # 3. Roles and Permissions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                permission_id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                risk_level TEXT NOT NULL -- LOW, MEDIUM, HIGH, CRITICAL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role TEXT NOT NULL,
                permission_id TEXT NOT NULL,
                PRIMARY KEY (role, permission_id),
                FOREIGN KEY (permission_id) REFERENCES permissions (permission_id)
            )
            """)

            # 4. Centralized Policies Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                policy_id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                decision TEXT NOT NULL, -- ALLOW, DENY, APPROVAL_REQUIRED
                conditions TEXT, -- JSON condition criteria
                created_at TEXT NOT NULL
            )
            """)

            # 5. Documents and Metadata Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                classification TEXT NOT NULL, -- PUBLIC_INTERNAL, ROLE_RESTRICTED, CONFIDENTIAL, HIGHLY_CONFIDENTIAL
                department TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                indexed_at TEXT,
                summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users (user_id)
            )
            """)

            # 6. Audit Trail Table (tamper-evident hash chain)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                role TEXT,
                session_id TEXT,
                request_id TEXT,
                event_type TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT,
                tool TEXT,
                decision TEXT,
                status TEXT NOT NULL, -- SUCCESS, FAILED, BLOCKED
                details TEXT, -- JSON payload without secrets
                prev_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL
            )
            """)

            # 7. Approvals (Human-in-the-loop) Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL, -- PENDING, APPROVED, REJECTED
                reviewer_id TEXT,
                decision_timestamp TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # 8. Model Registry Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_registry (
                model_id TEXT PRIMARY KEY,
                worker_type TEXT UNIQUE NOT NULL, -- organizer, general, coding, vision, document
                model_name TEXT NOT NULL,
                file_path TEXT,
                checksum TEXT,
                license TEXT NOT NULL,
                capabilities TEXT NOT NULL, -- JSON list
                vram_required_mb INTEGER NOT NULL,
                ram_required_mb INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'UNLOADED', -- UNLOADED, LOADING, READY, RUNNING, IDLE, UNLOADING
                last_loaded_at TEXT,
                last_inference_ms REAL DEFAULT 0.0
            )
            """)

            # 9. Workflows and Executions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                run_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                task_description TEXT NOT NULL,
                status TEXT NOT NULL, -- PENDING, PLANNING, EXECUTING, VERIFYING, COMPLETED, FAILED, BLOCKED
                current_step INTEGER DEFAULT 0,
                plan_json TEXT,
                result_summary TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # 10. Workflow Step Tracing Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_steps (
                step_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                step_number INTEGER NOT NULL,
                action_name TEXT NOT NULL,
                worker_type TEXT NOT NULL,
                tool_name TEXT,
                status TEXT NOT NULL, -- PENDING, RUNNING, COMPLETED, FAILED, RETRIED, SKIPPED
                input_data TEXT,
                output_data TEXT,
                verification_status TEXT, -- PASS, FAIL, RETRY, NEEDS_HUMAN_REVIEW
                latency_ms REAL DEFAULT 0.0,
                FOREIGN KEY (run_id) REFERENCES workflow_runs (run_id) ON DELETE CASCADE
            )
            """)

            conn.commit()


# Database Singleton Instance
DB = DatabaseManager()
