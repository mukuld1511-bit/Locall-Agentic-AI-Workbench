from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOME_ROOT = Path.home().resolve()


BLOCKED_COMMANDS = {
    "sudo",
    "su",
    "shutdown",
    "reboot",
    "poweroff",
    "mkfs",
    "fdisk",
    "mount",
    "umount",
    "passwd",
    "cryptsetup",
}


BLOCKED_PATTERNS = (
    "rm -rf /",
    "rm -rf ~",
    "rm -rf *",
    "dd if=",
    "> /dev/",
    "chmod -R 777 /",
    ":(){ :|:& };:",
)


def _is_safe_path(path: Path) -> bool:
    path = path.resolve()

    allowed_roots = (
        PROJECT_ROOT,
        HOME_ROOT,
    )

    return any(
        path == root or root in path.parents
        for root in allowed_roots
    )


def run_terminal(
    command: str,
    cwd: str | None = None,
    timeout: int = 60,
):
    """
    Controlled terminal execution.

    This is intentionally NOT unrestricted root/system access.
    Commands are executed as the logged-in desktop user and are
    restricted from obvious destructive system operations.
    """

    command = str(command or "").strip()

    if not command:
        return {
            "success": False,
            "returncode": 126,
            "stdout": "",
            "stderr": "Empty command.",
        }

    try:
        tokens = shlex.split(command)
    except Exception as exc:
        return {
            "success": False,
            "returncode": 126,
            "stdout": "",
            "stderr": f"Invalid command syntax: {exc}",
        }

    if tokens and tokens[0] in BLOCKED_COMMANDS:
        return {
            "success": False,
            "returncode": 126,
            "stdout": "",
            "stderr": "BLOCKED: privileged/destructive command.",
        }

    lowered = command.lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern in lowered:
            return {
                "success": False,
                "returncode": 126,
                "stdout": "",
                "stderr": f"BLOCKED: dangerous command pattern: {pattern}",
            }

    workdir = (
        Path(cwd).expanduser().resolve()
        if cwd
        else PROJECT_ROOT
    )

    if not workdir.exists() or not workdir.is_dir():
        return {
            "success": False,
            "returncode": 126,
            "stdout": "",
            "stderr": f"Invalid working directory: {workdir}",
        }

    # Workdir itself must remain in approved scope.
    if not _is_safe_path(workdir):
        return {
            "success": False,
            "returncode": 126,
            "stdout": "",
            "stderr": "Working directory outside approved scope.",
        }

    try:
        proc = subprocess.run(
            ["/bin/bash", "-lc", command],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=min(max(int(timeout), 1), 120),
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        )

        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": 124,
            "stdout": "",
            "stderr": "COMMAND TIMEOUT",
        }


def create_file_via_terminal(
    filename: str,
    directory: str | None = None,
    content: str = "",
):
    """
    Actual file creation using the controlled terminal layer.

    The target path is validated before shell execution.
    """

    directory_path = (
        Path(directory).expanduser().resolve()
        if directory
        else HOME_ROOT
    )

    if not _is_safe_path(directory_path):
        raise PermissionError(
            "Target directory is outside approved filesystem scope."
        )

    safe_name = Path(filename).name

    if safe_name != filename:
        raise PermissionError(
            "Path traversal is not allowed."
        )

    if not safe_name:
        raise ValueError(
            "Filename cannot be empty."
        )

    target = (
        directory_path / safe_name
    ).resolve()

    if target.parent != directory_path:
        raise PermissionError(
            "Invalid target path."
        )

    if target.exists():
        raise FileExistsError(
            f"File already exists: {target}"
        )

    # Python creates a quoted command for the terminal.
    # Content is sent through stdin rather than shell interpolation.
    command = (
        "python3 -c "
        "'import sys; "
        "from pathlib import Path; "
        f"p=Path({str(target)!r}); "
        "p.write_text(sys.stdin.read(), encoding=\"utf-8\")'"
    )

    result = subprocess.run(
        ["/bin/bash", "-lc", command],
        input=content,
        cwd=str(directory_path),
        capture_output=True,
        text=True,
        timeout=30,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "Terminal file creation failed."
        )

    return target


def read_file_via_terminal(path: str):
    target = Path(path).expanduser().resolve()

    if not _is_safe_path(target):
        raise PermissionError(
            "File is outside approved filesystem scope."
        )

    result = run_terminal(
        f"cat -- {shlex.quote(str(target))}",
        cwd=str(target.parent),
    )

    if not result["success"]:
        raise RuntimeError(
            result["stderr"]
        )

    return result["stdout"]


def list_directory_via_terminal(path: str):
    directory = Path(path).expanduser().resolve()

    if not _is_safe_path(directory):
        raise PermissionError(
            "Directory is outside approved filesystem scope."
        )

    result = run_terminal(
        "ls -la -- "
        + shlex.quote(str(directory)),
        cwd=str(directory),
    )

    if not result["success"]:
        raise RuntimeError(
            result["stderr"]
        )

    return result["stdout"]
