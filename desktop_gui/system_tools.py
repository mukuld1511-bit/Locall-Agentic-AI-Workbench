from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import List, Tuple

WORKBENCH_ROOT = Path.home() / "Locall-Agentic-AI-Workbench"
DATA_ROOT = WORKBENCH_ROOT / "data"

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
}

BLOCKED_PATTERNS = (
    "rm -rf /",
    "rm -rf ~",
    "rm -rf *",
    "dd if=",
    "chmod -R 777 /",
    ":(){:|:&};:",
    "> /dev/",
    "curl | sh",
    "wget | sh",
    "nc -e",
    "ncat -e",
)

def normalize_path(path: str) -> Path:
    if path.startswith("~"):
        p = Path(path).expanduser()
    else:
        p = Path(path).expanduser()

    return p.resolve()

def list_directory(path: str) -> List[Path]:
    p = normalize_path(path)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"Directory does not exist: {p}")

    return sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

def create_folder(parent: str, name: str) -> Path:
    parent_path = normalize_path(parent)

    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        raise ValueError("Invalid folder name.")

    target = (parent_path / name).resolve()
    target.mkdir(parents=False, exist_ok=False)
    return target

def is_blocked(command: str) -> Tuple[bool, str]:
    lowered = command.strip().lower()

    if not lowered:
        return True, "Empty command."

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return True, f"Invalid command syntax: {exc}"

    if tokens and tokens[0] in BLOCKED_COMMANDS:
        return True, f"Command '{tokens[0]}' is blocked."

    for pattern in BLOCKED_PATTERNS:
        if pattern in lowered:
            return True, f"Blocked command pattern: {pattern}"

    if "\x00" in command:
        return True, "NUL byte is not allowed."

    return False, ""

def run_safe_command(command: str, cwd: str, timeout: int = 30) -> Tuple[int, str, str]:
    blocked, reason = is_blocked(command)

    if blocked:
        return 126, "", f"BLOCKED: {reason}"

    workdir = normalize_path(cwd)

    if not workdir.exists() or not workdir.is_dir():
        return 126, "", f"Invalid working directory: {workdir}"

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        completed = subprocess.run(
            ["/bin/bash", "-lc", command],
            cwd=str(workdir),
            env=env,
            capture_output=True,
            text=True,
            timeout=max(1, min(timeout, 120)),
        )

        return completed.returncode, completed.stdout, completed.stderr

    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return 124, str(stdout), f"TIMEOUT\n{stderr}"
