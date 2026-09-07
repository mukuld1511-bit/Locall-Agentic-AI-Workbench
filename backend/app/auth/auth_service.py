"""Authentication Service for Sovereign Industrial AI Workbench.

Implements:
- FIPS-compliant PBKDF2-HMAC-SHA256 password hashing (100,000 iterations)
- Cryptographic salt generation (32 bytes)
- Constant-time comparison to prevent timing side-channel attacks
- Session generation with cryptographically secure tokens
- Account lockout after 5 consecutive failed attempts
- Complete audit logging on every authentication attempt
"""

import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from backend.app.database.db import DB
from backend.app.audit.audit_service import AUDIT
from backend.app.core.config import GLOBAL_CONFIG


class AuthService:
    def __init__(self):
        self.db = DB
        self.iterations = 100_000

    def hash_password(self, password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
        """Hashes a password with a cryptographically secure salt using PBKDF2."""
        if salt_hex is None:
            salt_bytes = os.urandom(32)
            salt_hex = salt_bytes.hex()
        else:
            salt_bytes = bytes.fromhex(salt_hex)
            
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt_bytes,
            self.iterations,
            dklen=64,
        )
        return key.hex(), salt_hex

    def verify_password(self, password: str, password_hash: str, salt_hex: str) -> bool:
        """Verifies a password using constant-time comparison."""
        computed_hash, _ = self.hash_password(password, salt_hex)
        return hmac.compare_digest(computed_hash, password_hash)

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        department: str,
        role: str,
        email: Optional[str] = None,
        operator_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a new user account with hashed credentials."""
        user_id = f"usr_{uuid.uuid4().hex[:8]}"
        password_hash, salt = self.hash_password(password)
        now = datetime.now(timezone.utc).isoformat()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (
                    user_id, username, full_name, email, department, role,
                    password_hash, salt, status, failed_attempts, locked_until,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', 0, NULL, ?, ?)
                """,
                (
                    user_id, username.lower().strip(), full_name, email,
                    department, role.upper(), password_hash, salt, now, now
                ),
            )
            conn.commit()

        AUDIT.log_event(
            event_type="USER_CREATED",
            action="create_user",
            status="SUCCESS",
            user_id=operator_user_id,
            resource=f"user:{user_id}",
            details={"created_username": username, "assigned_role": role, "department": department},
        )

        return {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "role": role,
            "department": department,
            "status": "ACTIVE",
        }

    def login(self, username: str, password: str, ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """Authenticates user, validates lockouts, and generates a session token."""
        username_clean = username.lower().strip()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username_clean,))
            user = cursor.fetchone()

            if not user:
                AUDIT.log_event(
                    event_type="LOGIN_FAILED",
                    action="authenticate",
                    status="FAILED",
                    details={"reason": "User not found", "attempted_username": username_clean},
                )
                return {"success": False, "error": "Invalid credentials"}

            # Check if account is DISABLED
            if user["status"] == "DISABLED":
                AUDIT.log_event(
                    event_type="LOGIN_BLOCKED",
                    action="authenticate",
                    status="BLOCKED",
                    user_id=user["user_id"],
                    details={"reason": "Account is disabled by administrator"},
                )
                return {"success": False, "error": "Account is disabled. Contact system administrator."}

            # Check if account is LOCKED
            if user["locked_until"]:
                locked_until_dt = datetime.fromisoformat(user["locked_until"])
                if now < locked_until_dt:
                    AUDIT.log_event(
                        event_type="LOGIN_BLOCKED",
                        action="authenticate",
                        status="BLOCKED",
                        user_id=user["user_id"],
                        details={"reason": "Account temporarily locked due to excessive failed attempts"},
                    )
                    remaining = int((locked_until_dt - now).total_seconds() / 60)
                    return {"success": False, "error": f"Account locked. Try again in {max(1, remaining)} minutes."}
                else:
                    # Lockout expired, reset status
                    cursor.execute(
                        "UPDATE users SET status = 'ACTIVE', failed_attempts = 0, locked_until = NULL WHERE user_id = ?",
                        (user["user_id"],),
                    )
                    conn.commit()

            # Verify password
            if not self.verify_password(password, user["password_hash"], user["salt"]):
                failed_attempts = user["failed_attempts"] + 1
                locked_until = None
                new_status = user["status"]

                if failed_attempts >= GLOBAL_CONFIG.MAX_LOGIN_ATTEMPTS:
                    lockout_time = now + timedelta(minutes=GLOBAL_CONFIG.LOCKOUT_DURATION_MINUTES)
                    locked_until = lockout_time.isoformat()
                    new_status = "LOCKED"

                cursor.execute(
                    "UPDATE users SET failed_attempts = ?, status = ?, locked_until = ? WHERE user_id = ?",
                    (failed_attempts, new_status, locked_until, user["user_id"]),
                )
                conn.commit()

                AUDIT.log_event(
                    event_type="LOGIN_FAILED",
                    action="authenticate",
                    status="FAILED",
                    user_id=user["user_id"],
                    details={"failed_attempts": failed_attempts, "locked": new_status == "LOCKED"},
                )

                if new_status == "LOCKED":
                    return {"success": False, "error": f"Maximum failed attempts exceeded. Account locked for {GLOBAL_CONFIG.LOCKOUT_DURATION_MINUTES} minutes."}
                return {"success": False, "error": "Invalid credentials"}

            # Authentication successful: reset failed attempts
            cursor.execute(
                "UPDATE users SET failed_attempts = 0, locked_until = NULL, updated_at = ? WHERE user_id = ?",
                (now_iso, user["user_id"]),
            )

            # Generate new session
            session_id = f"sess_{secrets.token_urlsafe(32)}"
            expires_at = (now + timedelta(hours=GLOBAL_CONFIG.SESSION_EXPIRY_HOURS)).isoformat()

            cursor.execute(
                """
                INSERT INTO sessions (
                    session_id, user_id, role, created_at, expires_at, is_active, last_activity
                ) VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (session_id, user["user_id"], user["role"], now_iso, expires_at, now_iso),
            )
            conn.commit()

        AUDIT.log_event(
            event_type="LOGIN_SUCCESS",
            action="authenticate",
            status="SUCCESS",
            user_id=user["user_id"],
            role=user["role"],
            session_id=session_id,
            details={"ip": ip_address, "department": user["department"]},
        )

        return {
            "success": True,
            "session_id": session_id,
            "user": {
                "user_id": user["user_id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "department": user["department"],
                "role": user["role"],
            },
            "expires_at": expires_at,
        }

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validates session token, ensuring it is active and unexpired."""
        if not session_id:
            return None

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.session_id, s.user_id, s.role, s.expires_at, s.is_active,
                       u.username, u.full_name, u.department, u.status as user_status
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.session_id = ?
                """,
                (session_id,),
            )
            row = cursor.fetchone()

            if not row or not row["is_active"]:
                return None

            if row["user_status"] != "ACTIVE":
                return None

            expires_at = datetime.fromisoformat(row["expires_at"])
            if now > expires_at:
                cursor.execute("UPDATE sessions SET is_active = 0 WHERE session_id = ?", (session_id,))
                conn.commit()
                AUDIT.log_event(
                    event_type="SESSION_EXPIRED",
                    action="validate_session",
                    status="EXPIRED",
                    user_id=row["user_id"],
                    session_id=session_id,
                )
                return None

            # Update last activity
            cursor.execute("UPDATE sessions SET last_activity = ? WHERE session_id = ?", (now_iso, session_id))
            conn.commit()

            return {
                "session_id": row["session_id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "department": row["department"],
                "role": row["role"],
            }

    def logout(self, session_id: str) -> bool:
        """Terminates session and records audit event."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, role FROM sessions WHERE session_id = ?", (session_id,))
            session = cursor.fetchone()
            if session:
                cursor.execute("UPDATE sessions SET is_active = 0 WHERE session_id = ?", (session_id,))
                conn.commit()
                AUDIT.log_event(
                    event_type="LOGOUT",
                    action="logout",
                    status="SUCCESS",
                    user_id=session["user_id"],
                    role=session["role"],
                    session_id=session_id,
                )
                return True
        return False


AUTH = AuthService()
