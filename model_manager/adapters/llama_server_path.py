from pathlib import Path
import os
import shutil

def _find_llama_server():
    candidates = []

    env_path = os.environ.get("LLAMA_SERVER")
    if env_path:
        candidates.append(Path(env_path))

    project_root = Path(__file__).resolve().parents[2]

    candidates.extend([
        project_root / "runtime" / "llama" / "llama-server.exe",
        project_root / "runtime" / "llama" / "llama-server",
    ])

    path_server = shutil.which("llama-server")
    if path_server:
        candidates.append(Path(path_server))

    candidates.append(Path("/home/piet/llama.cpp/build/bin/llama-server"))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


LLAMA_SERVER = _find_llama_server()

if LLAMA_SERVER is None:
    raise FileNotFoundError(
        "llama-server not found. "
        "Set LLAMA_SERVER or place llama-server in runtime/llama/"
    )

print("LLAMA_SERVER =", LLAMA_SERVER)
