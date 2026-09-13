from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_ROOT = ROOT / "runtime" / "sandbox"


def ensure_sandbox():
    SANDBOX_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )


def reset_sandbox():
    ensure_sandbox()

    for item in SANDBOX_ROOT.iterdir():
        if item.is_dir():
            import shutil
            shutil.rmtree(item)
        else:
            item.unlink()

    return SANDBOX_ROOT


def run_python(
    code: str,
    timeout: int = 30,
):
    ensure_sandbox()

    script = SANDBOX_ROOT / "main.py"

    script.write_text(
        str(code),
        encoding="utf-8",
    )

    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONUNBUFFERED": "1",
        "HOME": str(SANDBOX_ROOT),
        "TMPDIR": str(SANDBOX_ROOT),
    }

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(script),
            ],
            cwd=str(SANDBOX_ROOT),
            capture_output=True,
            text=True,
            timeout=max(
                1,
                min(timeout, 120),
            ),
            env=env,
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "path": str(script),
        }

    except subprocess.TimeoutExpired as exc:
        return {
            "success": False,
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": "Sandbox execution timed out.",
            "path": str(script),
        }


def list_sandbox_files():
    ensure_sandbox()

    return sorted(
        SANDBOX_ROOT.iterdir(),
        key=lambda x: (
            not x.is_dir(),
            x.name.lower(),
        ),
    )
