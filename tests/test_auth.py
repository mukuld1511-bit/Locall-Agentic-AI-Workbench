"""Unit and Security Tests for Authentication Subsystem."""

import unittest
import time
from backend.app.database.db import DB
from backend.app.auth.auth_service import AUTH
from backend.app.core.config import GLOBAL_CONFIG


class TestAuthSubsystem(unittest.TestCase):
    def setUp(self):
        DB.init_schema()

    def test_password_hashing_and_verification(self):
        password = "ConfidentialPlantPassword@2026"
        pwd_hash, salt = AUTH.hash_password(password)
        self.assertNotEqual(password, pwd_hash)
        self.assertTrue(AUTH.verify_password(password, pwd_hash, salt))
        self.assertFalse(AUTH.verify_password("WrongPassword123", pwd_hash, salt))

    def test_successful_login_and_session(self):
        res = AUTH.login("operator_101", "Operator@123!")
        self.assertTrue(res["success"])
        self.assertIn("session_id", res)
        self.assertEqual(res["user"]["role"], "GRADE_1")

        # Validate session
        session_data = AUTH.validate_session(res["session_id"])
        self.assertIsNotNone(session_data)
        self.assertEqual(session_data["username"], "operator_101")

        # Logout
        self.assertTrue(AUTH.logout(res["session_id"]))
        self.assertIsNone(AUTH.validate_session(res["session_id"]))

    def test_account_lockout_after_consecutive_failures(self):
        # Create dedicated test user with unique name
        username = f"lockout_user_{int(time.time() * 1000)}"
        AUTH.create_user(username, "SafePassword123!", "Test Operator", "Ops", "GRADE_1")

        # Trigger 5 failed logins
        for i in range(GLOBAL_CONFIG.MAX_LOGIN_ATTEMPTS):
            res = AUTH.login(username, "WrongPassword!")
            self.assertFalse(res["success"])

        # 6th attempt should be blocked due to account lockout
        res = AUTH.login(username, "SafePassword123!")
        self.assertFalse(res["success"])
        self.assertIn("Account locked", res["error"])


if __name__ == "__main__":
    unittest.main()
