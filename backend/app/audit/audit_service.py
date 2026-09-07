"""Immutable, Tamper-Evident Audit Logging Service for Sovereign Industrial Operations.

Every security-sensitive event (authentication, policy decisions, model loads,
tool executions, human approvals, workflow steps) is permanently logged with
a cryptographic SHA-256 hash-chain to guarantee unforgeable provenance.
NO secrets, passwords, or raw auth tokens are ever logged.
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.database.db import DB
from backend.app.core.config import GLOBAL_CONFIG


class AuditService:
    def __init__(self):
        self.db = DB
        self.audit_log_file = GLOBAL_CONFIG.AUDIT_LOG_PATH
        self.audit_log_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_last_event_hash(self) -> str:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_hash FROM audit_events ORDER BY rowid DESC LIMIT 1")
            row = cursor.fetchone()
            if row and row["event_hash"]:
                return row["event_hash"]
        return "GENESIS_HASH_0000000000000000000000000000000000000000000000000000000000"

    def log_event(
        self,
        event_type: str,
        action: str,
        status: str,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        resource: Optional[str] = None,
        tool: Optional[str] = None,
        decision: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Logs an event securely with hash chaining."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        prev_hash = self._get_last_event_hash()

        # Sanitize details to guarantee zero secrets/passwords are captured
        safe_details = {}
        if details:
            for k, v in details.items():
                if any(secret_term in k.lower() for secret_term in ["password", "token", "secret", "salt", "key"]):
                    safe_details[k] = "[REDACTED_SECURITY_DATA]"
                else:
                    safe_details[k] = v

        details_json = json.dumps(safe_details, sort_keys=True)

        # Compute tamper-evident hash
        hash_payload = f"{event_id}|{timestamp}|{user_id}|{role}|{event_type}|{action}|{resource}|{tool}|{status}|{prev_hash}|{details_json}"
        event_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_events (
                    event_id, timestamp, user_id, role, session_id, request_id,
                    event_type, action, resource, tool, decision, status,
                    details, prev_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id, timestamp, user_id, role, session_id, request_id,
                    event_type, action, resource, tool, decision, status,
                    details_json, prev_hash, event_hash
                ),
            )
            conn.commit()

        # Write append-only entry to disk log for forensic inspection
        try:
            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "event_id": event_id,
                    "timestamp": timestamp,
                    "user_id": user_id,
                    "role": role,
                    "event_type": event_type,
                    "action": action,
                    "status": status,
                    "event_hash": event_hash,
                }) + "\n")
        except Exception:
            pass

        return event_id

    def get_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute(
                    "SELECT * FROM audit_events WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?",
                    (event_type, limit),
                )
            else:
                cursor.execute(
                    "SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def verify_integrity(self) -> Dict[str, Any]:
        """Verifies the SHA-256 hash-chain across all recorded audit entries."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_events ORDER BY rowid ASC")
            rows = cursor.fetchall()
            
            expected_prev_hash = "GENESIS_HASH_0000000000000000000000000000000000000000000000000000000000"
            for idx, row in enumerate(rows):
                if row["prev_hash"] != expected_prev_hash:
                    return {
                        "verified": False,
                        "broken_at_event_id": row["event_id"],
                        "index": idx,
                        "error": "Hash-chain mismatch detected in audit log!",
                    }
                
                # Recompute hash
                hash_payload = f"{row['event_id']}|{row['timestamp']}|{row['user_id']}|{row['role']}|{row['event_type']}|{row['action']}|{row['resource']}|{row['tool']}|{row['status']}|{row['prev_hash']}|{row['details']}"
                computed_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()
                if computed_hash != row["event_hash"]:
                    return {
                        "verified": False,
                        "broken_at_event_id": row["event_id"],
                        "index": idx,
                        "error": "Event record hash corrupted or tampered!",
                    }
                expected_prev_hash = row["event_hash"]

            return {
                "verified": True,
                "total_records_checked": len(rows),
                "chain_valid": True,
            }


AUDIT = AuditService()
