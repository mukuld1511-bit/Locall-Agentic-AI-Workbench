from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home().resolve()

ALLOWED_ROOTS = (
    HOME,
    PROJECT_ROOT,
)

BLOCKED_COMMANDS = {
    "sudo",
    "su",
    "shutdown",
    "reboot",
    "poweroff",
    "halt",
    "mkfs",
    "fdisk",
    "parted",
    "mount",
    "umount",
    "cryptsetup",
}

BLOCKED_PATTERNS = (
    "rm -rf /",
    "rm -rf ~",
    "rm -rf /*",
    "dd if=",
    ":(){",
    "chmod -R 777 /",
    "chown -R root",
    "> /dev/",
)


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def allowed_path(path: str | Path) -> bool:
    target = resolve_path(path)

    return any(
        target == root or root in target.parents
        for root in ALLOWED_ROOTS
    )


def ensure_allowed(path: str | Path):
    target = resolve_path(path)

    if not allowed_path(target):
        raise PermissionError(
            f"PC access denied outside approved scope: {target}"
        )

    return target


def read_file(path: str | Path) -> str:
    target = ensure_allowed(path)

    if not target.is_file():
        raise FileNotFoundError(str(target))

    return target.read_text(
        encoding="utf-8",
        errors="replace",
    )


def write_file(
    path: str | Path,
    content: str,
    overwrite: bool = True,
) -> str:

    target = ensure_allowed(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if target.exists() and not overwrite:
        raise FileExistsError(str(target))

    target.write_text(
        str(content),
        encoding="utf-8",
    )

    if not target.exists():
        raise RuntimeError(
            f"Write verification failed: {target}"
        )

    return str(target)


def create_file(
    path: str | Path,
    content: str = "",
) -> str:

    target = ensure_allowed(path)

    if target.exists():
        raise FileExistsError(
            f"Already exists: {target}"
        )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        str(content),
        encoding="utf-8",
    )

    if not target.is_file():
        raise RuntimeError(
            f"Creation verification failed: {target}"
        )

    return str(target)


def delete_file(
    path: str | Path,
) -> str:

    target = ensure_allowed(path)

    if target in {
        HOME,
        PROJECT_ROOT,
    }:
        raise PermissionError(
            "Deleting an approved root directory is blocked."
        )

    if not target.exists():
        raise FileNotFoundError(str(target))

    if target.is_dir():
        raise PermissionError(
            "Recursive directory deletion is blocked by default."
        )

    target.unlink()

    if target.exists():
        raise RuntimeError(
            f"Delete verification failed: {target}"
        )

    return str(target)


def move_file(
    source: str | Path,
    destination: str | Path,
) -> str:

    src = ensure_allowed(source)
    dst = ensure_allowed(destination)

    if not src.exists():
        raise FileNotFoundError(str(src))

    dst.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.move(
        str(src),
        str(dst),
    )

    final = dst.resolve()

    if not final.exists():
        raise RuntimeError(
            "Move verification failed."
        )

    return str(final)


def copy_file(
    source: str | Path,
    destination: str | Path,
) -> str:

    src = ensure_allowed(source)
    dst = ensure_allowed(destination)

    if not src.is_file():
        raise FileNotFoundError(str(src))

    dst.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        str(src),
        str(dst),
    )

    if not dst.exists():
        raise RuntimeError(
            "Copy verification failed."
        )

    return str(dst.resolve())


def list_directory(
    path: str | Path = HOME,
):
    directory = ensure_allowed(path)

    if not directory.is_dir():
        raise NotADirectoryError(
            str(directory)
        )

    result = []

    for item in sorted(
        directory.iterdir(),
        key=lambda x: (
            not x.is_dir(),
            x.name.lower(),
        ),
    ):
        result.append({
            "name": item.name,
            "path": str(item),
            "type": "directory"
            if item.is_dir()
            else "file",
            "size": (
                item.stat().st_size
                if item.is_file()
                else None
            ),
        })

    return result


def run_command(
    command: str,
    cwd: str | Path = PROJECT_ROOT,
    timeout: int = 60,
):
    command = str(command or "").strip()

    if not command:
        raise ValueError(
            "Empty command."
        )

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(
            f"Invalid command: {exc}"
        )

    if tokens and tokens[0] in BLOCKED_COMMANDS:
        raise PermissionError(
            f"Blocked command: {tokens[0]}"
        )

    lowered = command.lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern in lowered:
            raise PermissionError(
                f"Blocked dangerous command pattern: {pattern}"
            )

    workdir = ensure_allowed(cwd)

    if not workdir.is_dir():
        raise NotADirectoryError(
            str(workdir)
        )

    proc = subprocess.run(
        [
            "/bin/bash",
            "-lc",
            command,
        ],
        cwd=str(workdir),
        capture_output=True,
        text=True,
        timeout=min(
            max(int(timeout), 1),
            180,
        ),
        env={
            **os.environ,
            "PYTHONUNBUFFERED": "1",
        },
    )

    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "success": proc.returncode == 0,
    }


def open_path(
    path: str | Path,
):
    target = ensure_allowed(path)

    if not target.exists():
        raise FileNotFoundError(str(target))

    subprocess.Popen(
        [
            "xdg-open",
            str(target),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return str(target)


def open_url(url: str):
    url = str(url).strip()

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        raise ValueError(
            "Only HTTP/HTTPS URLs are allowed."
        )

    webbrowser.open(url)

    return url
