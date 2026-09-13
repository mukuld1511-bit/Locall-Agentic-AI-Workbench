import requests
import json
import unittest

BASE_URL = "http://127.0.0.1:8088"

class TestRBACWatertight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Login as operator_101 (GRADE_1)
        r_op = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "operator_101", "password": "demo123"})
        data_op = r_op.json()
        assert data_op["success"], f"Operator login failed: {data_op}"
        cls.op_session = data_op["session_id"]
        cls.op_headers = {"Authorization": f"Bearer {cls.op_session}", "Content-Type": "application/json"}

        # 2. Login as engineer_202 (GRADE_2)
        r_eng = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "engineer_202", "password": "demo123"})
        data_eng = r_eng.json()
        assert data_eng["success"], f"Engineer login failed: {data_eng}"
        cls.eng_session = data_eng["session_id"]
        cls.eng_headers = {"Authorization": f"Bearer {cls.eng_session}", "Content-Type": "application/json"}

        # 3. Login as superintendent_303 (GRADE_3)
        r_supt = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "superintendent_303", "password": "demo123"})
        data_supt = r_supt.json()
        assert data_supt["success"], f"Superintendent login failed: {data_supt}"
        cls.supt_session = data_supt["session_id"]
        cls.supt_headers = {"Authorization": f"Bearer {cls.supt_session}", "Content-Type": "application/json"}

        # 4. Login as admin (ADMIN)
        r_admin = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "admin123"})
        data_admin = r_admin.json()
        assert data_admin["success"], f"Admin login failed: {data_admin}"
        cls.admin_session = data_admin["session_id"]
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_session}", "Content-Type": "application/json"}

    def test_01_unauthenticated_rejects(self):
        """Unauthenticated requests with fake token must fail closed with 401."""
        fake_headers = {"Authorization": "Bearer fake_malicious_token_xyz"}
        r = requests.post(f"{BASE_URL}/api/files/write", json={"path": "test.txt", "content": "hack"}, headers=fake_headers)
        self.assertEqual(r.status_code, 401)

    def test_02_operator_terminal_blocked(self):
        """Grade 1 Operator MUST be blocked from running terminal commands."""
        r = requests.post(f"{BASE_URL}/api/terminal/run", json={"command": "whoami"}, headers=self.op_headers)
        res = r.json()
        self.assertFalse(res.get("success", False))
        self.assertIn("PERMISSION DENIED", res.get("stderr", ""))

    def test_03_operator_sandbox_blocked(self):
        """Grade 1 Operator MUST be blocked from running sandbox code."""
        r = requests.post(f"{BASE_URL}/api/sandbox/exec", json={"code": "print('hello')", "language": "python"}, headers=self.op_headers)
        res = r.json()
        self.assertFalse(res.get("success", False))
        self.assertIn("PERMISSION DENIED", res.get("stderr", ""))

    def test_04_operator_file_write_blocked(self):
        """Grade 1 Operator MUST be blocked from modifying workspace files."""
        r = requests.post(f"{BASE_URL}/api/files/write", json={"path": "src/dummy.txt", "content": "tamper"}, headers=self.op_headers)
        self.assertEqual(r.status_code, 403)
        self.assertIn("PERMISSION DENIED", r.json().get("error", ""))

    def test_05_operator_file_create_blocked(self):
        """Grade 1 Operator MUST be blocked from creating workspace files."""
        r = requests.post(f"{BASE_URL}/api/files/create", json={"path": "src/hacked.py", "content": "import os"}, headers=self.op_headers)
        self.assertEqual(r.status_code, 403)
        self.assertIn("PERMISSION DENIED", r.json().get("error", ""))

    def test_06_operator_db_custom_query_blocked(self):
        """Grade 1 Operator MUST be blocked from executing custom SQL queries."""
        r = requests.post(f"{BASE_URL}/api/db/demo/query", json={"query": "SELECT * FROM equipment"}, headers=self.op_headers)
        self.assertEqual(r.status_code, 403)
        self.assertIn("SECURITY POLICY VIOLATION", r.json().get("error", ""))

    def test_07_operator_file_read_allowed(self):
        """Grade 1 Operator is allowed to read SOPs and workspace files."""
        r = requests.post(f"{BASE_URL}/api/files/read", json={"path": "package.json"}, headers=self.op_headers)
        self.assertEqual(r.status_code, 200)
        self.assertIn("content", r.json())

    def test_08_path_traversal_blocked(self):
        """Directory traversal escaping workspace MUST be blocked."""
        r = requests.post(f"{BASE_URL}/api/files/read", json={"path": "../../Windows/win.ini"}, headers=self.eng_headers)
        self.assertEqual(r.status_code, 403)
        self.assertIn("escapes allowed workspace", r.json().get("error", ""))

    def test_09_engineer_sandbox_and_terminal_allowed(self):
        """Grade 2 Engineer CAN run sandbox code and safe terminal diagnostics."""
        r_box = requests.post(f"{BASE_URL}/api/sandbox/exec", json={"code": "print('ENGINEER_SAFE_CALC')", "language": "python"}, headers=self.eng_headers)
        self.assertTrue(r_box.json().get("success", False))
        self.assertIn("ENGINEER_SAFE_CALC", r_box.json().get("stdout", ""))

        r_term = requests.post(f"{BASE_URL}/api/terminal/run", json={"command": "echo ENG_DIAG_OK"}, headers=self.eng_headers)
        self.assertTrue(r_term.json().get("success", False))
        self.assertIn("ENG_DIAG_OK", r_term.json().get("stdout", ""))

    def test_10_engineer_file_delete_blocked(self):
        """Grade 2 Engineer MUST NOT be allowed to delete workspace files."""
        r = requests.post(f"{BASE_URL}/api/files/delete", json={"path": "src/dummy.txt"}, headers=self.eng_headers)
        self.assertEqual(r.status_code, 403)

    def test_11_engineer_db_drop_table_blocked_by_ro_sqlite(self):
        """Attempting DROP TABLE on presentation DB must fail under read-only policy."""
        r = requests.post(f"{BASE_URL}/api/db/demo/query", json={"query": "DROP TABLE equipment"}, headers=self.eng_headers)
        self.assertEqual(r.status_code, 403)

    def test_12_non_admin_employee_create_blocked(self):
        """Only ADMIN can register employees. Grade 2/3 must be blocked."""
        payload = {"username": "test_rogue", "password": "password123", "full_name": "Rogue User", "department": "Operations", "role": "GRADE_1"}
        r_eng = requests.post(f"{BASE_URL}/api/employees/create", json=payload, headers=self.eng_headers)
        self.assertEqual(r_eng.status_code, 403)

        r_supt = requests.post(f"{BASE_URL}/api/employees/create", json=payload, headers=self.supt_headers)
        self.assertEqual(r_supt.status_code, 403)

    def test_13_admin_employee_create_allowed(self):
        """ADMIN can register employees."""
        import uuid
        unique_user = f"emp_{uuid.uuid4().hex[:6]}"
        payload = {"username": unique_user, "password": "password123", "full_name": "Verified Operator", "department": "CDU/VDU Operations", "role": "GRADE_1"}
        r = requests.post(f"{BASE_URL}/api/employees/create", json=payload, headers=self.admin_headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("status"), "ok")

if __name__ == "__main__":
    unittest.main()
