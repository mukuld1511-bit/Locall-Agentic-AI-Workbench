import os
import zipfile
from pathlib import Path

# Paths
ROOT = Path(r"C:\AI\Locall-Agentic-AI-Workbench").resolve()
OUTPUT_ZIP = Path(r"C:\AI\Sovereign-Industrial-AI-Workbench-DGX.zip")

EXCLUDE_DIRS = {
    ".venv",
    "node_modules",
    ".git",
    "__pycache__",
    ".gemini",
    ".idea",
    ".vscode"
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo"
}

print(f"[*] Packaging project from {ROOT} to {OUTPUT_ZIP}...")

if OUTPUT_ZIP.exists():
    OUTPUT_ZIP.unlink()

count = 0
with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(ROOT):
        # Exclude directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in EXCLUDE_EXTS:
                continue
            if file_path == OUTPUT_ZIP:
                continue

            rel_path = file_path.relative_to(ROOT)
            zipf.write(file_path, arcname=str(rel_path))
            count += 1

size_mb = round(OUTPUT_ZIP.stat().st_size / (1024 * 1024), 2)
print(f"[+] Successfully packed {count} files into {OUTPUT_ZIP} ({size_mb} MB)!")
