"""Tests for Tool Gateway, Schema Validation, and Isolated Sandbox Execution."""

import unittest
from tools.gateway import TOOL_GATEWAY
from tools.sandbox.sandbox_runner import SANDBOX


class TestToolGatewayAndSandbox(unittest.TestCase):
    def test_schema_validation_missing_arguments(self):
        # sandbox_exec requires {"code": ...}
        res = TOOL_GATEWAY.execute_tool(
            tool_name="sandbox_exec",
            arguments={},  # Missing 'code'
            user_id="usr_eng",
            role="GRADE_2",
        )
        self.assertFalse(res["success"])
        self.assertIn("Missing required parameter", res["error"])

    def test_safe_math_execution_in_sandbox(self):
        code = "val = 42 * 2\nprint(f'RESULT={val}')"
        res = SANDBOX.execute_python(code)
        self.assertTrue(res["success"])
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("RESULT=84", res["stdout"])

    def test_network_access_blocked_in_sandbox(self):
        # Code attempting outbound network connection must be blocked
        network_code = "import socket\ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\ns.connect(('8.8.8.8', 53))"
        res = SANDBOX.execute_python(network_code)
        self.assertFalse(res["success"])
        self.assertIn("PermissionError", res["stderr"])
        self.assertIn("Network communication is disabled", res["stderr"])

    def test_infinite_loop_timeout_in_sandbox(self):
        # Execution must terminate cleanly upon reaching timeout
        infinite_loop = "while True: pass"
        res = SANDBOX.execute_python(infinite_loop, custom_timeout=2)
        self.assertFalse(res["success"])
        self.assertTrue(res["timed_out"])
        self.assertIn("timed out", res["stderr"])


if __name__ == "__main__":
    unittest.main()
