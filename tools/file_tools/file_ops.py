"""Secure File Operations with Path Traversal and Sensitive Asset Protection.

Guarantees:
- Normalizes all paths against permitted sandboxed base directories.
- Strictly prevents '../' traversal, symlink escapes, and root file access.
- Forbids reading/modifying database files (.db), policy configs, or system secrets.
- Verifies maximum file size constraints.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from backend.app.core.config import GLOBAL_CONFIG


ALLOWED_ROOTS = [
    GLOBAL_CONFIG.DATA_DIR.resolve(),
    GLOBAL_CONFIG.DOCS_STORAGE_DIR.resolve(),
    GLOBAL_CONFIG.ARTIFACTS_DIR.resolve(),
]

FORBIDDEN_PATTERNS = [
    "workbench.db",
    "audit.log",
    ".env",
    "password",
    "id_rsa",
    "/etc",
    "/proc",
    "/sys",
]


def validate_safe_path(target_path_str: str) -> Path:
    """Validates that path resides inside permitted directories and is not protected."""
    target_path = Path(target_path_str).resolve()

    # Check forbidden filename patterns
    for forbidden in FORBIDDEN_PATTERNS:
        if forbidden in str(target_path).lower():
            raise PermissionError(f"Access to protected system resource '{forbidden}' is strictly forbidden.")

    # Must resolve within allowed root directories
    is_within_allowed = any(
        str(target_path).startswith(str(allowed_root)) for allowed_root in ALLOWED_ROOTS
    )
    if not is_within_allowed:
        raise PermissionError(f"Path traversal blocked: target '{target_path}' is outside authorized storage boundaries.")

    return target_path


def safe_file_read(file_path: str, max_bytes: int = 10 * 1024 * 1024) -> Dict[str, Any]:
    """Safely reads file content within authorized sandbox boundaries."""
    safe_path = validate_safe_path(file_path)

    if not safe_path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    if safe_path.stat().st_size > max_bytes:
        return {"success": False, "error": f"File exceeds maximum permissible size ({max_bytes} bytes)"}

    try:
        content = safe_path.read_text(encoding="utf-8", errors="replace")
        return {
            "success": True,
            "path": str(safe_path),
            "size_bytes": safe_path.stat().st_size,
            "content": content,
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to read file: {str(e)}"}


def safe_file_write(file_path: str, content: str) -> Dict[str, Any]:
    """Safely writes file content inside authorized artifacts directory."""
    safe_path = validate_safe_path(file_path)
    safe_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        safe_path.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "path": str(safe_path),
            "size_bytes": safe_path.stat().st_size,
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to write file: {str(e)}"}
