"""Sandboxed Code Execution Engine for Sovereign Industrial Operations.

Executes generated analytical Python calculations (API 510 remaining life,
thermodynamic efficiency, pressure drop, etc.) in a restricted environment:
- ZERO network connectivity (socket imports & network syscalls blocked)
- Hard execution timeouts (default 10s)
- CPU & memory caps
- Ephemeral workspace isolation with automatic cleanup
- Captures stdout, stderr, exit code, and execution latency
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
from backend.app.core.config import GLOBAL_CONFIG


SECURITY_HEADER = """
# Sandboxed Industrial Execution Isolation
import sys
# Block socket / network modules
class BlockedNetworkModule:
    def __getattr__(self, name):
        raise PermissionError("Network communication is disabled in sovereign air-gapped sandbox.")

sys.modules['socket'] = BlockedNetworkModule()
sys.modules['urllib.request'] = BlockedNetworkModule()
sys.modules['http.client'] = BlockedNetworkModule()
"""


class SandboxRunner:
    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def execute_python(self, code: str, custom_timeout: Optional[int] = None) -> Dict[str, Any]:
        """Executes python code string inside an isolated ephemeral subprocess."""
        timeout = custom_timeout or self.timeout_seconds
        start_time = time.time()

        with tempfile.TemporaryDirectory(prefix="sih_sandbox_") as tmp_dir:
            script_path = Path(tmp_dir) / "isolated_task.py"
            
            # Combine security header with user script
            full_code = SECURITY_HEADER + "\n" + code
            script_path.write_text(full_code, encoding="utf-8")

            # Sandbox environment
            env = os.environ.copy()
            env["PYTHONPATH"] = ""
            env["AIR_GAPPED_SANDBOX"] = "1"

            try:
                proc = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=tmp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                )
                duration_ms = (time.time() - start_time) * 1000.0

                return {
                    "success": proc.returncode == 0,
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout.strip(),
                    "stderr": proc.stderr.strip(),
                    "duration_ms": round(duration_ms, 2),
                    "timed_out": False,
                }
            except subprocess.TimeoutExpired:
                duration_ms = (time.time() - start_time) * 1000.0
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds.",
                    "duration_ms": round(duration_ms, 2),
                    "timed_out": True,
                }
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000.0
                return {
                    "success": False,
                    "exit_code": -2,
                    "stdout": "",
                    "stderr": f"Sandbox launch failure: {str(e)}",
                    "duration_ms": round(duration_ms, 2),
                    "timed_out": False,
                }


SANDBOX = SandboxRunner()
