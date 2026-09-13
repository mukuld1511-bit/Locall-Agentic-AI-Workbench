from __future__ import annotations

import re
import uuid

import threading
import subprocess
import os
import uuid
from pathlib import Path

import customtkinter as ctk


# ============================================================
# CTK SCROLL COMPATIBILITY
# ============================================================
#
# Some CustomTkinter versions receive event.widget as a Tk
# widget-path string. The internal _mouse_wheel_all handler
# expects a real widget object and then accesses .master,
# which causes:
#
#   AttributeError: 'str' object has no attribute 'master'
#
# Convert the widget path safely before CustomTkinter handles it.
# ============================================================

try:
    from customtkinter.windows.widgets import (
        ctk_scrollable_frame,
    )

    _original_check_if_valid_scroll = (
        ctk_scrollable_frame.CTkScrollableFrame
        ._check_if_valid_scroll
    )

    def _safe_check_if_valid_scroll(
        self,
        widget,
    ):
        try:

            if isinstance(widget, str):

                try:
                    root = self.winfo_toplevel()
                    widget = root.nametowidget(
                        widget
                    )
                except Exception:
                    # If the path cannot be resolved, simply
                    # tell CTk that the widget is not a valid
                    # scroll target rather than crashing.
                    return False

            return _original_check_if_valid_scroll(
                self,
                widget,
            )

        except Exception:
            return False

    ctk_scrollable_frame.CTkScrollableFrame \
        ._check_if_valid_scroll = \
        _safe_check_if_valid_scroll

except Exception:
    # UI compatibility patch is optional; never prevent app
    # startup because of it.
    pass
from tkinter import filedialog, messagebox

try:
    from PIL import Image
except Exception:
    Image = None
    ImageTk = None

from .chat_service import ChatService
from .conversation_state import ConversationState
from .semantic_organizer import SemanticOrganizer

from .sandbox_service import (
    ensure_sandbox,
    reset_sandbox,
    run_python,
    list_sandbox_files,
)
from .file_context import read_file

from .file_edit_agent import (
    detect_file_edit_request,
    resolve_edit_target,
    clean_edited_content,
    overwrite_verified_file,
)

from .file_agent import (
    detect_file_request,
    clean_file_content,
    unique_path,
    basic_fallback,
    generate_prompt,
    write_verified_file,
)
from .safe_tools import (
    run_terminal,
    create_file_via_terminal,
    read_file_via_terminal,
    list_directory_via_terminal,
)


ROOT = Path(__file__).resolve().parents[1]

# DEVELOPMENT / DEMO MODE
# Set False to restore normal authentication.
DEV_AUTH_BYPASS = True

DEV_USER = {
    "user_id": "usr_demo_local",
    "username": "mukul",
    "role": "ADMIN",
}


def tool_create_file(
    path: str,
    content: str = "",
):
    """
    Chat -> actual filesystem bridge.

    The coding model generates the content.
    This function performs the real file write.
    """

    target = Path(path).expanduser().resolve()

    home = Path.home().resolve()
    project = ROOT.resolve()

    allowed = (
        target == home
        or home in target.parents
        or target == project
        or project in target.parents
    )

    if not allowed:
        raise PermissionError(
            "File creation outside approved local scope is blocked."
        )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Prevent accidental overwrite unless explicitly intended.
    if target.exists():
        raise FileExistsError(
            f"File already exists: {target}"
        )

    target.write_text(
        str(content),
        encoding="utf-8",
    )

    # Verify the actual filesystem side effect.
    if not target.exists() or not target.is_file():
        raise RuntimeError(
            f"File creation verification failed: {target}"
        )

    return target


try:
    from backend.app.auth.auth_service import AuthService
except Exception:
    AuthService = None

try:
    from backend.app.database.db import DB
except Exception:
    DB = None

try:
    from backend.app.workflows.workflow_engine import WORKFLOW_ENGINE
except Exception:
    WORKFLOW_ENGINE = None

try:
    from backend.app.audit.audit_service import AUDIT
except Exception:
    AUDIT = None


MODEL_MGR = None


def model_manager():
    global MODEL_MGR

    if MODEL_MGR is None:
        try:
            from model_manager.manager import MODEL_MGR as mm
            MODEL_MGR = mm
        except Exception:
            return None

    return MODEL_MGR


def ensure_db():
    if DB:
        try:
            DB.init_schema()
        except Exception:
            pass



def detect_intent(text: str, has_file: bool = False) -> str:
    q = text.lower().strip()

    # Explicit filesystem actions must happen through a tool,
    # not through a language-model explanation.
    filesystem = (
        "create file",
        "create a file",
        "make a file",
        "generate a file",
        "write a file",
        "save a file",
        "create an empty file",
        "make an empty file",
    )

    if any(x in q for x in filesystem):
        return "file_action"

    if any(x in q for x in (
        "run command",
        "execute command",
        "execute this",
        "run this in terminal",
        "open terminal",
    )):
        return "tool"

    if has_file and any(x in q for x in (
        "image",
        "photo",
        "picture",
        "diagram",
        "p&id",
        "look at",
        "what is in this image",
        "analyze this image",
    )):
        return "vision"

    if has_file and any(x in q for x in (
        "read this",
        "read file",
        "summarize this",
        "summarize the file",
        "extract from",
        "analyze this document",
        "analyze the report",
    )):
        return "document"

    if any(x in q for x in (
        "html",
        "css",
        "javascript",
        "three.js",
        "threejs",
    )):
        return "coding"

    if any(x in q for x in (
        "python",
        "code",
        "script",
        "program",
        "function",
        "debug",
        "sql",
        "javascript",
        "java",
        "c++",
    )):
        return "coding"

    if any(x in q for x in (
        "inspection",
        "corrosion",
        "remaining life",
        "efficiency",
        "thermodynamic",
        "approval note",
        "p&id",
        "safety verification",
    )):
        return "workflow"

    return "general"



def risky(text: str):
    q = text.lower()

    return any(x in q for x in [
        "delete production",
        "drop database",
        "shutdown plant",
        "change production",
        "bypass safety",
        "disable security",
        "modify firewall",
        "delete database",
        "format disk",
        "sudo",
    ])



def clean_ai_output(text: str) -> str:
    text = str(text or "")

    for token in (
        "<|im_end|>",
        "<|im_start|>",
        "<|endoftext|>",
    ):
        text = text.replace(token, "")

    text = re.sub(
        r"^\s*Assistant\s*:\s*",
        "",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"\n+\s*I hope this helps!?[\s\S]*$",
        "",
        text,
        flags=re.I,
    )

    return text.strip()



def execute_file_action(request: str):
    q = request.lower()

    if "home directory" not in q and "home folder" not in q:
        raise PermissionError(
            "File creation is currently restricted to the home directory."
        )

    extension = ".txt"

    for ext in (
        ".py",
        ".txt",
        ".json",
        ".md",
        ".csv",
        ".log",
    ):
        if ext in q:
            extension = ext
            break

    filename = None

    patterns = [
        r"(?:named|called)\s+([A-Za-z0-9_.-]+)",
        r"(?:file)\s+([A-Za-z0-9_.-]+\.(?:py|txt|json|md|csv|log))",
    ]

    for pattern in patterns:
        m = re.search(
            pattern,
            request,
            flags=re.I,
        )
        if m:
            filename = m.group(1)
            break

    if not filename:
        filename = "new_file" + extension

    filename = Path(filename).name

    if not filename.lower().endswith(extension):
        filename += extension

    home = Path.home().resolve()
    target = (home / filename).resolve()

    if target.parent != home:
        raise PermissionError(
            "Invalid file path."
        )

    if target.exists():
        raise FileExistsError(
            f"File already exists: {target}"
        )

    target.touch()

    return target



def detect_terminal_action(text: str):
    q = text.lower().strip()

    # Actual file-system actions.
    if any(x in q for x in (
        "create a file",
        "create file",
        "make a file",
        "generate a file",
        "write a file",
        "save a file",
        "create an empty file",
        "make an empty file",
    )):
        return "file_create"

    if any(x in q for x in (
        "list files",
        "list my files",
        "show files",
        "show directory",
        "list directory",
    )):
        return "file_list"

    if any(x in q for x in (
        "read this file",
        "cat this file",
        "read file",
    )):
        return "file_read"

    if any(x in q for x in (
        "run this command",
        "run command",
        "execute command",
        "execute this in terminal",
        "open terminal and",
    )):
        return "terminal"

    return None


def parse_file_creation_request(text: str):
    extension = ".txt"
    q = text.lower()

    for ext in (
        ".py",
        ".txt",
        ".json",
        ".md",
        ".csv",
        ".log",
        ".yaml",
        ".yml",
    ):
        if ext in q:
            extension = ext
            break

    filename = None

    for pattern in (
        r"(?:named|called)\s+([A-Za-z0-9_.-]+)",
        r"file\s+([A-Za-z0-9_.-]+\.(?:py|txt|json|md|csv|log|yaml|yml))",
    ):
        m = re.search(
            pattern,
            text,
            flags=re.I,
        )

        if m:
            filename = m.group(1)
            break

    if not filename:
        filename = "new_file" + extension

    filename = Path(filename).name

    if not filename.lower().endswith(extension):
        filename += extension

    return {
        "filename": filename,
        "directory": str(Path.home()),
    }



def detect_file_generation_request(text: str):
    """
    Detect requests where the user wants an actual file generated.
    Works for common code/document/web file types.
    """

    q = text.lower().strip()

    intent_phrases = (
        "generate a file",
        "generate file",
        "generate a python file",
        "generate a py file",
        "generate a html file",
        "generate an html file",
        "generate a css file",
        "generate a js file",
        "generate a javascript file",
        "generate a json file",
        "generate a markdown file",
        "create a file",
        "create a python file",
        "create a py file",
        "create a html file",
        "create an html file",
        "create a css file",
        "create a js file",
        "create a javascript file",
        "make a file",
        "make a python file",
        "make an html file",
        "write a file",
        "save this as a file",
    )

    if not any(
        phrase in q
        for phrase in intent_phrases
    ):
        return None

    # --------------------------------------------------------
    # EXTENSION
    # --------------------------------------------------------

    extension_map = {
        ".py": ".py",
        ".python": ".py",
        ".html": ".html",
        ".htm": ".html",
        ".css": ".css",
        ".js": ".js",
        ".javascript": ".js",
        ".ts": ".ts",
        ".json": ".json",
        ".md": ".md",
        ".markdown": ".md",
        ".txt": ".txt",
        ".csv": ".csv",
        ".yaml": ".yaml",
        ".yml": ".yml",
        ".xml": ".xml",
        ".sql": ".sql",
        ".sh": ".sh",
    }

    extension = None

    for token, ext in extension_map.items():
        if token in q:
            extension = ext
            break

    if extension is None:

        if "python" in q or " py " in f" {q} ":
            extension = ".py"

        elif "html" in q:
            extension = ".html"

        elif "css" in q:
            extension = ".css"

        elif "javascript" in q or " js " in f" {q} ":
            extension = ".js"

        elif "json" in q:
            extension = ".json"

        elif "markdown" in q:
            extension = ".md"

        else:
            extension = ".txt"

    # --------------------------------------------------------
    # TARGET DIRECTORY
    # --------------------------------------------------------

    directory = Path.home()

    if "downloads" in q:
        directory = Path.home() / "Downloads"

    elif "desktop" in q:
        directory = Path.home() / "Desktop"

    elif "documents" in q:
        directory = Path.home() / "Documents"

    elif "home directory" in q or "home folder" in q:
        directory = Path.home()

    # --------------------------------------------------------
    # FILENAME
    # --------------------------------------------------------

    filename = None

    patterns = (
        r"(?:named|called)\s+([A-Za-z0-9_.-]+)",
        r"(?:file)\s+([A-Za-z0-9_.-]+\.[A-Za-z0-9_-]+)",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.I,
        )

        if match:

            candidate = Path(
                match.group(1)
            ).name

            # Don't accidentally treat a location word as filename.
            if candidate.lower() not in {
                "in",
                "home",
                "downloads",
                "desktop",
                "directory",
                "folder",
            }:
                filename = candidate
                break

    if not filename:

        filename = (
            "generated_file"
            + extension
        )

    filename = Path(
        filename
    ).name

    # Correct extension if user says "python file" but filename
    # omitted extension.
    if "." not in Path(filename).name:
        filename += extension

    return {
        "target": (
            directory / filename
        ).expanduser().resolve(),
        "extension": extension,
        "filename": filename,
    }


def clean_generated_file_content(text: str) -> str:
    """
    Convert model output into actual file content.
    """

    text = str(text or "").strip()

    # Remove model chat-template artifacts.
    for token in (
        "<|im_end|>",
        "<|im_start|>",
        "<|endoftext|>",
    ):
        text = text.replace(token, "")

    text = re.sub(
        r"^\s*Assistant\s*:\s*",
        "",
        text,
        flags=re.I,
    )

    # Remove one surrounding markdown fence.
    fenced = re.match(
        r"^```(?:python|py|javascript|js|json|text)?\s*"
        r"([\s\S]*?)"
        r"\s*```$",
        text,
        flags=re.I,
    )

    if fenced:
        text = fenced.group(1).strip()

    return text.strip()



def default_file_content(
    extension: str,
    request: str = "",
) -> str:

    ext = (extension or ".txt").lower()
    q = str(request or "").lower()

    if ext in (".html", ".htm"):

        if "three" in q or "3d" in q:

            return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Three.js Scene</title>
<style>
html, body {
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #0b1020;
    font-family: Arial, sans-serif;
}
canvas {
    display: block;
}
.overlay {
    position: fixed;
    top: 24px;
    left: 24px;
    padding: 16px 20px;
    color: white;
    background: rgba(12, 18, 35, 0.7);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 14px;
    backdrop-filter: blur(12px);
    z-index: 10;
}
</style>
</head>
<body>
<div class="overlay">
    <strong>Three.js Scene</strong><br>
    <span>Local generated webpage</span>
</div>

<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script>
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b1020);

const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    100
);
camera.position.z = 5;

const renderer = new THREE.WebGLRenderer({
    antialias: true
});
renderer.setPixelRatio(
    Math.min(window.devicePixelRatio, 2)
);
renderer.setSize(
    window.innerWidth,
    window.innerHeight
);
document.body.appendChild(
    renderer.domElement
);

const light = new THREE.PointLight(
    0xffffff,
    2
);
light.position.set(
    2,
    3,
    4
);
scene.add(light);

scene.add(
    new THREE.AmbientLight(
        0x8899bb,
        1.5
    )
);

const geometry = new THREE.IcosahedronGeometry(
    1.2,
    2
);

const material = new THREE.MeshStandardMaterial({
    color: 0x4f8cff,
    metalness: 0.35,
    roughness: 0.25
});

const mesh = new THREE.Mesh(
    geometry,
    material
);

scene.add(mesh);

function animate() {
    requestAnimationFrame(animate);

    mesh.rotation.x += 0.005;
    mesh.rotation.y += 0.008;

    renderer.render(
        scene,
        camera
    );
}

animate();

window.addEventListener(
    "resize",
    () => {
        camera.aspect =
            window.innerWidth /
            window.innerHeight;

        camera.updateProjectionMatrix();

        renderer.setSize(
            window.innerWidth,
            window.innerHeight
        );
    }
);
</script>
</body>
</html>
"""

        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Generated Page</title>
<style>
body {
    margin: 0;
    min-height: 100vh;
    display: grid;
    place-items: center;
    font-family: Arial, sans-serif;
    background: #f5f7fa;
}
main {
    padding: 40px;
    text-align: center;
}
</style>
</head>
<body>
<main>
    <h1>Generated HTML Page</h1>
    <p>Your local AI workbench created this file.</p>
</main>
</body>
</html>
"""

    if ext == ".py":
        return """def main():
    print("Generated Python file")


if __name__ == "__main__":
    main()
"""

    if ext == ".css":
        return """/* Generated stylesheet */

:root {
    font-family: Arial, sans-serif;
}

body {
    margin: 0;
}
"""

    if ext == ".js":
        return """// Generated JavaScript file

console.log("Generated JavaScript file");
"""

    if ext == ".json":
        return """{
  "generated": true,
  "source": "Sovereign Industrial AI Workbench"
}
"""

    if ext == ".md":
        return """# Generated Document

Created by Sovereign Industrial AI Workbench.
"""

    return ""



def bind_safe_mousewheel(widget):
    """
    Bind mouse-wheel scrolling safely to the supplied widget.

    Avoids CustomTkinter's global _mouse_wheel_all handler,
    which can retain destroyed Tk widget references.
    """

    def on_wheel(event):

        try:

            # Linux / generic Tk wheel handling.
            delta = event.delta

            if delta == 0:
                return "break"

            units = -1 if delta > 0 else 1

            widget.yview_scroll(
                units,
                "units",
            )

        except Exception:
            # Never let a UI wheel event crash the GUI.
            pass

        return "break"

    def on_linux_up(event):
        try:
            widget.yview_scroll(
                -3,
                "units",
            )
        except Exception:
            pass
        return "break"

    def on_linux_down(event):
        try:
            widget.yview_scroll(
                3,
                "units",
            )
        except Exception:
            pass
        return "break"

    try:
        widget.bind(
            "<MouseWheel>",
            on_wheel,
            add="+",
        )

        widget.bind(
            "<Button-4>",
            on_linux_up,
            add="+",
        )

        widget.bind(
            "<Button-5>",
            on_linux_down,
            add="+",
        )

    except Exception:
        pass

    return widget



def clean_model_output(
    output: str,
    extension: str = ".txt",
) -> str:

    text = str(
        output or ""
    ).replace(
        "\r\n",
        "\n",
    ).strip()

    for token in (
        "<|im_start|>",
        "<|im_end|>",
        "<|endoftext|>",
        "<|eot_id|>",
        "<|start_header_id|>",
        "<|end_header_id|>",
    ):
        text = text.replace(
            token,
            "",
        )

    # Cut recursive transcript generation.
    markers = (
        "\nUSER:",
        "\nASSISTANT:",
        "\nuser:",
        "\nassistant:",
        "\nUSER ",
        "\nASSISTANT ",
    )

    for marker in markers:

        pos = text.find(marker)

        if pos > 0:
            text = text[:pos]

    # Remove leading assistant labels.
    while text.lower().startswith(
        "assistant:"
    ):
        text = text[
            len("assistant:"):
        ].lstrip()

    # Remove one code fence when applicable.
    fence = re.match(
        r"^\s*```[A-Za-z0-9_+-]*\s*\n?"
        r"([\s\S]*?)"
        r"\n?```\s*$",
        text,
        flags=re.I,
    )

    if fence:
        text = fence.group(1).strip()

    return text.strip()



def normalize_model_answer(text: str) -> str:
    """
    Protect the UI from common small-model generation failures:
    repeated transcript headers, repeated assistant prefixes,
    control tokens and runaway duplicated blocks.
    """

    text = str(
        text or ""
    ).replace(
        "\r\n",
        "\n",
    ).strip()

    for token in (
        "<|im_start|>",
        "<|im_end|>",
        "<|endoftext|>",
        "<|eot_id|>",
        "<|start_header_id|>",
        "<|end_header_id|>",
    ):
        text = text.replace(
            token,
            "",
        )

    # Strip leading assistant labels.
    text = re.sub(
        r"^\s*(assistant|ASSISTANT)\s*:\s*",
        "",
        text,
    )

    # Stop if model starts manufacturing a new turn.
    turn = re.search(
        r"\n\s*(USER|ASSISTANT)\s*:",
        text,
        flags=re.I,
    )

    if turn:
        text = text[:turn.start()].rstrip()

    # Detect pathological immediate repetition.
    lines = text.splitlines()
    cleaned = []

    previous = None
    repeat_count = 0

    for line in lines:

        normalized = " ".join(
            line.strip().lower().split()
        )

        if not normalized:
            cleaned.append(line)
            continue

        if normalized == previous:
            repeat_count += 1

            # Never allow a runaway repeated line.
            if repeat_count >= 2:
                continue

        else:
            repeat_count = 0

        cleaned.append(line)
        previous = normalized

    return "\n".join(
        cleaned
    ).strip()



def resolve_ui_intent(
    text: str,
    *,
    attachment_path=None,
    previous_intent=None,
    previous_file=None,
    previous_directory=None,
):
    """
    Single UI-side intent entry point.

    The SemanticOrganizer is authoritative. Attachment metadata is
    supplied as context so phrases such as "what is it" can resolve
    against the selected image/document.
    """

    organizer = SemanticOrganizer(model_manager)

    # Organizer API in this project accepts request/context fields.
    try:

        result = organizer.organize(
            text,
            state=None,
            attachment=attachment_path,
            previous_intent=previous_intent,
            previous_file=previous_file,
            previous_directory=previous_directory,
        )

    except TypeError:

        # Compatibility with older organizer signatures.
        try:
            result = organizer.organize(
                text,
                state=None,
            )
        except TypeError:
            result = organizer.organize(
                text,
            )

    return result


class Login(ctk.CTkFrame):

    def __init__(self, parent, on_success):
        super().__init__(
            parent,
            fg_color="#f5f7fa",
        )

        self.on_success = on_success
        self._busy = False

        self.grid_columnconfigure(
            (0, 1),
            weight=1,
        )
        self.grid_rowconfigure(
            0,
            weight=1,
        )

        left = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=16,
        )
        left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(45, 12),
            pady=45,
        )

        ctk.CTkLabel(
            left,
            text="SOVEREIGN\nINDUSTRIAL AI",
            text_color="#2563eb",
            font=ctk.CTkFont(
                size=30,
                weight="bold",
            ),
            justify="left",
        ).pack(
            anchor="w",
            padx=36,
            pady=(40, 8),
        )

        ctk.CTkLabel(
            left,
            text=(
                "SECURE LOCAL INDUSTRIAL INTELLIGENCE\n"
                "for engineering and operations"
            ),
            text_color="#77818d",
            justify="left",
        ).pack(
            anchor="w",
            padx=36,
        )

        ctk.CTkFrame(
            left,
            fg_color="transparent",
        ).pack(
            fill="both",
            expand=True,
        )

        for t in [
            "● LOCAL RUNTIME",
            "● SECURITY ENFORCED",
            "● AUDIT ENABLED",
        ]:
            ctk.CTkLabel(
                left,
                text=t,
                text_color="#16875a",
                font=ctk.CTkFont(
                    size=11,
                    weight="bold",
                ),
            ).pack(
                anchor="w",
                padx=36,
                pady=3,
            )

        right = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=16,
        )
        right.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(12, 45),
            pady=45,
        )

        ctk.CTkLabel(
            right,
            text="Welcome back",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(
            anchor="w",
            padx=36,
            pady=(42, 5),
        )

        ctk.CTkLabel(
            right,
            text="Sign in to your local workbench.",
            text_color="#77818d",
        ).pack(
            anchor="w",
            padx=36,
            pady=(0, 24),
        )

        ctk.CTkLabel(
            right,
            text="USERNAME",
            text_color="#77818d",
            font=ctk.CTkFont(
                size=10,
                weight="bold",
            ),
        ).pack(
            anchor="w",
            padx=36,
        )

        self.username = ctk.CTkEntry(
            right,
            height=40,
            corner_radius=9,
            placeholder_text="Username",
        )
        self.username.pack(
            fill="x",
            padx=36,
            pady=(5, 14),
        )

        ctk.CTkLabel(
            right,
            text="PASSWORD",
            text_color="#77818d",
            font=ctk.CTkFont(
                size=10,
                weight="bold",
            ),
        ).pack(
            anchor="w",
            padx=36,
        )

        self.password = ctk.CTkEntry(
            right,
            height=40,
            corner_radius=9,
            placeholder_text="Password",
            show="•",
        )
        self.password.pack(
            fill="x",
            padx=36,
            pady=(5, 8),
        )

        self.error = ctk.CTkLabel(
            right,
            text="",
            text_color="#c43d49",
            wraplength=330,
            justify="left",
        )
        self.error.pack(
            anchor="w",
            padx=36,
        )

        self.button = ctk.CTkButton(
            right,
            text="SIGN IN",
            height=42,
            corner_radius=9,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.login,
        )
        self.button.pack(
            fill="x",
            padx=36,
            pady=(10, 4),
        )

        self.status = ctk.CTkLabel(
            right,
            text="Local authentication",
            text_color="#77818d",
            font=ctk.CTkFont(size=10),
        )
        self.status.pack(
            anchor="w",
            padx=36,
        )

        self.password.bind(
            "<Return>",
            lambda _: self.login(),
        )

    def login(self):

        if self._busy:
            return

        username = self.username.get().strip()
        password = self.password.get()

        if not username or not password:
            self.error.configure(
                text="Enter username and password."
            )
            return

        if AuthService is None:
            self.error.configure(
                text="Authentication service unavailable."
            )
            return

        self._busy = True

        self.button.configure(
            state="disabled",
            text="SIGNING IN…",
        )

        self.status.configure(
            text="Authenticating locally…"
        )

        def worker():

            try:
                result = AuthService().login(
                    username,
                    password,
                )

                def done():
                    self._busy = False
                    self.button.configure(
                        state="normal",
                        text="SIGN IN",
                    )

                    if result.get("success"):
                        self.on_success(result)
                    else:
                        self.error.configure(
                            text=result.get(
                                "error",
                                "Invalid credentials",
                            )
                        )
                        self.status.configure(
                            text="Authentication failed"
                        )

                self.after(0, done)

            except Exception as exc:

                self.after(
                    0,
                    lambda error=str(exc): (self.error.configure(text=error
                        ),
                        self.status.configure(
                            text="Authentication error"
                        ),
                        self.button.configure(
                            state="normal",
                            text="SIGN IN",
                        )
                    ),
                )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()


class Workbench(ctk.CTkFrame):

    def __init__(self, parent, user):
        super().__init__(
            parent,
            fg_color="#f5f7fa",
        )

        self.user = user
        self.current_state = None
        self.chat_service = ChatService()

        self.conversation_state = ConversationState()

        self.semantic_organizer = SemanticOrganizer(
            model_manager,
        )
        self.chat_id = self.chat_service.new_chat(
            user.get(
                "user_id",
                user.get("username", "local"),
            )
        )

        self.attached_file = None
        self.attachment_kind = None
        self.attachment_name = None
        self.attachment_size = 0
        self.attachment_thumbnail = None
        self.last_created_file = None
        self.pending_intent = None
        self.busy = False
        self.sandbox_language = "python"

        self.grid_columnconfigure(
            1,
            weight=1,
        )
        self.grid_rowconfigure(
            0,
            weight=1,
        )

        self.build_sidebar()
        self.build_main()

        self.show_chat()

    def build_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=190,
            corner_radius=0,
            fg_color="#ffffff",
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="SOVEREIGN\nWORKBENCH",
            text_color="#2563eb",
            font=ctk.CTkFont(
                size=17,
                weight="bold",
            ),
            justify="left",
        ).pack(
            anchor="w",
            padx=20,
            pady=(24, 28),
        )

        for name in [
            "Chat",
            "Files",
            "IDE",
            "Sandbox",
            "Workflow",
            "Models",
            "Employees",
            "Audit",
            "Tools",
        ]:

            btn = ctk.CTkButton(
                self.sidebar,
                text=name,
                height=38,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#edf4ff",
                text_color="#77818d",
                anchor="w",
                command=lambda n=name: self.navigate(n),
            )

            btn.pack(
                fill="x",
                padx=12,
                pady=3,
            )

            setattr(
                self,
                f"nav_{name.lower()}",
                btn,
            )

        ctk.CTkLabel(
            self.sidebar,
            text=(
                f"{self.user.get('username', 'local')}\n"
                f"{self.user.get('role', 'UNKNOWN')}\n\n"
                "LOCAL ONLY"
            ),
            text_color="#77818d",
            font=ctk.CTkFont(size=9),
            justify="left",
        ).pack(
            side="bottom",
            anchor="w",
            padx=20,
            pady=20,
        )

    def build_main(self):

        self.main = ctk.CTkFrame(
            self,
            fg_color="#f5f7fa",
            corner_radius=0,
        )

        self.main.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=0,
            pady=0,
        )

        self.main.grid_columnconfigure(
            0,
            weight=1,
        )
        self.main.grid_rowconfigure(
            1,
            weight=1,
        )

        self.header = ctk.CTkFrame(
            self.main,
            height=56,
            fg_color="#ffffff",
            corner_radius=0,
        )

        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        ctk.CTkLabel(
            self.header,
            text="SOVEREIGN INDUSTRIAL AI WORKBENCH",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
        ).pack(
            side="left",
            padx=18,
            pady=12,
        )

        ctk.CTkLabel(
            self.header,
            text="● LOCAL",
            text_color="#16875a",
            font=ctk.CTkFont(
                size=10,
                weight="bold",
            ),
        ).pack(
            side="left",
        )

    def clear_page(self):

        for child in self.main.winfo_children():

            if child is not self.header:
                child.destroy()

    def navigate(self, name):

        if name == "Chat":
            self.show_chat()
        elif name == "Files":
            self.show_files()
        elif name == "Workflow":
            self.show_workflow()
        elif name == "Models":
            self.show_models()
        elif name == "Employees":
            self.show_employees()
        elif name == "Audit":
            self.show_audit()
        elif name == "IDE":
            self.show_ide()
        elif name == "Sandbox":
            self.show_sandbox()
        elif name == "Tools":
            self.show_tools()

    def show_chat(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=14,
            pady=12,
        )

        page.grid_columnconfigure(
            1,
            weight=1,
        )

        page.grid_rowconfigure(
            1,
            weight=1,
        )

        # ====================================================
        # CHAT HISTORY SIDEBAR
        # ====================================================

        history_panel = ctk.CTkFrame(
            page,
            width=245,
            fg_color="#ffffff",
            border_color="#e4e8ee",
            border_width=1,
            corner_radius=12,
        )

        history_panel.grid(
            row=0,
            column=0,
            rowspan=2,
            sticky="nsew",
            padx=(0, 10),
        )

        history_panel.grid_propagate(False)

        top_history = ctk.CTkFrame(
            history_panel,
            fg_color="transparent",
        )

        top_history.pack(
            fill="x",
            padx=10,
            pady=10,
        )

        ctk.CTkLabel(
            top_history,
            text="Chats",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=16,
                weight="bold",
            ),
        ).pack(
            side="left",
        )

        ctk.CTkButton(
            top_history,
            text="+",
            width=34,
            height=30,
            corner_radius=7,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.new_chat,
        ).pack(
            side="right",
        )

        self.chat_list = ctk.CTkScrollableFrame(
            history_panel,
            fg_color="transparent",
        )

        bind_safe_mousewheel(
            self.chat_list._parent_canvas
            if hasattr(
                self.chat_list,
                "_parent_canvas",
            )
            else self.chat_list
        )

        self.chat_list.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=(0, 8),
        )

        # ====================================================
        # CHAT HEADER
        # ====================================================

        top = ctk.CTkFrame(
            page,
            fg_color="transparent",
        )

        top.grid(
            row=0,
            column=1,
            sticky="ew",
        )

        ctk.CTkLabel(
            top,
            text="Chat",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(
            side="left",
        )

        ctk.CTkLabel(
            top,
            text=(
                "Persistent conversations · "
                "local context"
            ),
            text_color="#77818d",
            font=ctk.CTkFont(
                size=10,
            ),
        ).pack(
            side="left",
            padx=12,
        )

        ctk.CTkLabel(
            top,
            text="● LOCAL",
            text_color="#16875a",
            font=ctk.CTkFont(
                size=10,
                weight="bold",
            ),
        ).pack(
            side="right",
            padx=(0, 8),
        )

        self.mode = ctk.CTkOptionMenu(
            top,
            values=[
                "Auto",
                "General",
                "Coding",
                "Vision",
                "Workflow",
            ],
            width=120,
            height=34,
        )

        self.mode.set("Auto")

        self.mode.pack(
            side="right",
        )

        # ====================================================
        # CHAT DISPLAY
        # ====================================================

        history = ctk.CTkFrame(
            page,
            fg_color="#ffffff",
            border_color="#e4e8ee",
            border_width=1,
            corner_radius=12,
        )

        history.grid(
            row=1,
            column=1,
            sticky="nsew",
            pady=(8, 8),
        )

        history.grid_columnconfigure(
            0,
            weight=1,
        )

        history.grid_rowconfigure(
            0,
            weight=1,
        )

        self.chat_box = ctk.CTkTextbox(
            history,
            fg_color="#ffffff",
            border_width=0,
            text_color="#17202a",
            font=ctk.CTkFont(
                size=12,
            ),
            wrap="word",
        )

        self.chat_box.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10,
        )

        # History should be read-only.
        self.chat_box.configure(
            state="disabled"
        )

        # ====================================================
        # COMPOSER
        # ====================================================

        composer = ctk.CTkFrame(
            page,
            fg_color="#ffffff",
            border_color="#e4e8ee",
            border_width=1,
            corner_radius=12,
        )

        composer.grid(
            row=2,
            column=1,
            sticky="ew",
        )

        composer.grid_columnconfigure(
            0,
            weight=1,
        )

        self.entry = ctk.CTkTextbox(
            composer,
            height=88,
            fg_color="#fbfcfe",
            border_color="#e4e8ee",
            border_width=1,
            text_color="#17202a",
            font=ctk.CTkFont(
                size=12,
            ),
            wrap="word",
        )

        self.entry.grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="ew",
            padx=10,
            pady=(10, 8),
        )

        self.entry.bind(
            "<Return>",
            self.handle_enter,
        )

        # Explicit clipboard shortcuts.
        self.entry.bind(
            "<Control-c>",
            lambda e: self._clipboard_action(e, "<<Copy>>"),
        )

        self.entry.bind(
            "<Control-v>",
            lambda e: self._clipboard_action(e, "<<Paste>>"),
        )

        self.entry.bind(
            "<Control-x>",
            lambda e: self._clipboard_action(e, "<<Cut>>"),
        )

        self.entry.bind(
            "<Control-a>",
            lambda e: self._select_all(e),
        )

        # Linux alternate paste.
        self.entry.bind(
            "<Control-Shift-v>",
            lambda e: self._clipboard_action(e, "<<Paste>>"),
        )

        self.attach_button = ctk.CTkButton(
            composer,
            text="＋ Attach",
            width=100,
            height=34,
            fg_color="#ffffff",
            hover_color="#edf4ff",
            text_color="#17202a",
            border_color="#e4e8ee",
            border_width=1,
            command=self.attach,
        )

        self.attach_button.grid(
            row=1,
            column=0,
            padx=10,
            pady=(0, 10),
            sticky="w",
        )

        self.file_label = ctk.CTkLabel(
            composer,
            text="No file attached",
            text_color="#77818d",
            font=ctk.CTkFont(
                size=10,
            ),
        )

        self.file_label.grid(
            row=1,
            column=1,
            sticky="w",
        )

        ctk.CTkLabel(
            composer,
            text="Enter ↵ · Shift+Enter newline",
            text_color="#77818d",
            font=ctk.CTkFont(
                size=9,
            ),
        ).grid(
            row=1,
            column=2,
            padx=10,
        )

        self.send_button = ctk.CTkButton(
            composer,
            text="Send",
            width=90,
            height=36,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.send,
        )

        self.send_button.grid(
            row=1,
            column=3,
            padx=10,
            pady=(0, 10),
        )

        # Load saved conversations.
        self.refresh_chat_list()

        # Then load current chat.
        self.load_history()

    def _clipboard_action(self, event, action):
        try:
            event.widget.event_generate(action)
        except Exception:
            pass

        return "break"

    def _select_all(self, event):
        try:
            event.widget.tag_add(
                "sel",
                "1.0",
                "end-1c",
            )
        except Exception:
            pass

        return "break"


    def handle_enter(self, event):

        if event.state & 0x0001:
            return

        self.send()

        return "break"

    def load_history(self):

        if not hasattr(
            self,
            "chat_box",
        ):
            return

        self.chat_box.configure(
            state="normal"
        )

        self.chat_box.delete(
            "1.0",
            "end",
        )

        uid = self.user.get(
            "user_id",
            self.user.get(
                "username",
                "local",
            ),
        )

        try:

            rows = self.chat_service.messages(
                self.chat_id,
                uid,
                100,
            )

            for role, content, model, _ in rows:

                self.chat_box.insert(
                    "end",
                    f"{role.upper()}\n"
                    f"{content}\n\n",
                )

        except Exception:
            pass

        self.chat_box.configure(
            state="disabled"
        )

    def refresh_chat_list(self):

        if not hasattr(
            self,
            "chat_list",
        ):
            return

        for child in self.chat_list.winfo_children():
            child.destroy()

        try:
            bind_safe_mousewheel(
                self.chat_list._parent_canvas
                if hasattr(
                    self.chat_list,
                    "_parent_canvas",
                )
                else self.chat_list
            )
        except Exception:
            pass

        uid = self.user.get(
            "user_id",
            self.user.get(
                "username",
                "local",
            ),
        )

        try:
            chats = self.chat_service.list_chats(
                uid,
                100,
            )
        except Exception:
            chats = []

        if not chats:

            ctk.CTkLabel(
                self.chat_list,
                text="No conversations yet",
                text_color="#77818d",
                font=ctk.CTkFont(
                    size=10,
                ),
            ).pack(
                padx=8,
                pady=12,
            )

            return

        for chat_id, title, created, updated in chats:

            active = (
                chat_id == self.chat_id
            )

            btn = ctk.CTkButton(
                self.chat_list,
                text=title[:28],
                height=36,
                corner_radius=7,
                anchor="w",
                fg_color="#edf4ff"
                if active
                else "transparent",
                hover_color="#edf4ff",
                text_color="#2563eb"
                if active
                else "#17202a",
                command=lambda cid=chat_id:
                    self.open_chat(cid),
            )

            btn.pack(
                fill="x",
                padx=3,
                pady=2,
            )

    def new_chat(self):

        uid = self.user.get(
            "user_id",
            self.user.get(
                "username",
                "local",
            ),
        )

        self.chat_id = self.chat_service.new_chat(
            uid,
            "New Chat",
        )

        self.attached_file = None

        if hasattr(
            self,
            "file_label",
        ):
            self.file_label.configure(
                text="No file attached"
            )

        self.refresh_chat_list()
        self.load_history()

        if hasattr(
            self,
            "entry",
        ):
            self.entry.focus_set()

    def open_chat(self, chat_id):

        uid = self.user.get(
            "user_id",
            self.user.get(
                "username",
                "local",
            ),
        )

        # Only switch to conversations owned by this user.
        allowed = any(
            row[0] == chat_id
            for row in self.chat_service.list_chats(
                uid,
                1000,
            )
        )

        if not allowed:
            return

        self.chat_id = chat_id

        self.attached_file = None

        self.refresh_chat_list()
        self.load_history()

        if hasattr(
            self,
            "entry",
        ):
            self.entry.focus_set()


    def add_message(self, title, text):

        if not hasattr(
            self,
            "chat_box",
        ):
            return

        self.chat_box.configure(
            state="normal"
        )

        self.chat_box.insert(
            "end",
            f"{title}\n{text}\n\n",
        )

        self.chat_box.see(
            "end"
        )

        self.chat_box.configure(
            state="disabled"
        )







    def _ensure_attachment_widgets(self):

        # Reuse the same card for every attachment.
        if hasattr(
            self,
            "attachment_card",
        ):

            try:
                if self.attachment_card.winfo_exists():
                    return
            except Exception:
                pass

        # ----------------------------------------------------
        # REAL BUTTON -> REAL PARENT
        # ----------------------------------------------------

        attach_button = getattr(
            self,
            "attach_button",
            None,
        )

        if attach_button is None:
            raise RuntimeError(
                "Attach button reference is unavailable."
            )

        parent = attach_button.master

        if parent is None:
            raise RuntimeError(
                "Attach button parent is unavailable."
            )

        # ----------------------------------------------------
        # CARD
        # ----------------------------------------------------

        self.attachment_card = ctk.CTkFrame(
            parent,
            fg_color="#f7f9fc",
            border_color="#d8e1eb",
            border_width=1,
            corner_radius=10,
            height=50,
        )

        # IMPORTANT:
        # The existing composer uses GRID, so use GRID.
        attach_info = attach_button.grid_info()

        row = int(
            attach_info.get(
                "row",
                1,
            )
        )

        column = int(
            attach_info.get(
                "column",
                0,
            )
        )

        self.attachment_card.grid(
            row=row,
            column=column + 1,
            padx=(0, 8),
            pady=(0, 10),
            sticky="ew",
        )

        try:
            parent.grid_columnconfigure(
                column + 1,
                weight=1,
            )
        except Exception:
            pass

        # ----------------------------------------------------
        # IMAGE / FILE PREVIEW
        # ----------------------------------------------------

        self.attachment_preview = ctk.CTkLabel(
            self.attachment_card,
            text="📎",
            width=40,
            height=40,
            corner_radius=8,
            fg_color="#eaf2ff",
            text_color="#2563eb",
            font=ctk.CTkFont(
                size=16,
            ),
        )

        self.attachment_preview.pack(
            side="left",
            padx=(6, 8),
            pady=5,
        )

        # ----------------------------------------------------
        # INFO
        # ----------------------------------------------------

        info = ctk.CTkFrame(
            self.attachment_card,
            fg_color="transparent",
        )

        info.pack(
            side="left",
            fill="x",
            expand=True,
            pady=5,
        )

        self.file_label = ctk.CTkLabel(
            info,
            text="",
            text_color="#17202a",
            anchor="w",
            font=ctk.CTkFont(
                size=10,
                weight="bold",
            ),
        )

        self.file_label.pack(
            anchor="w",
        )

        self.file_meta = ctk.CTkLabel(
            info,
            text="",
            text_color="#748297",
            anchor="w",
            font=ctk.CTkFont(
                size=8,
            ),
        )

        self.file_meta.pack(
            anchor="w",
        )

        # ----------------------------------------------------
        # REMOVE
        # ----------------------------------------------------

        self.remove_attachment_button = ctk.CTkButton(
            self.attachment_card,
            text="×",
            width=30,
            height=30,
            corner_radius=7,
            fg_color="transparent",
            hover_color="#fee2e2",
            text_color="#64748b",
            font=ctk.CTkFont(
                size=16,
                weight="bold",
            ),
            command=self.clear_attachment,
        )

        self.remove_attachment_button.pack(
            side="right",
            padx=(4, 7),
        )

        # Hidden initially.
        self.attachment_card.grid_remove()

        self.attachment_thumbnail = None

        print(
            "[OK] Attachment card created in real composer:",
            parent.winfo_class(),
        )


    def attach(self):

        # Make sure the persistent attachment widgets exist.
        self._ensure_attachment_widgets()

        path = filedialog.askopenfilename(
            title="Attach image or file",
            filetypes=[
                (
                    "Images",
                    "*.png *.jpg *.jpeg *.webp *.bmp *.gif",
                ),
                (
                    "Documents",
                    "*.pdf *.doc *.docx *.ppt *.pptx *.txt *.md",
                ),
                (
                    "Spreadsheets",
                    "*.xlsx *.xls *.csv *.tsv",
                ),
                (
                    "Databases",
                    "*.db *.sqlite *.sqlite3",
                ),
                (
                    "Code",
                    "*.py *.js *.ts *.html *.css *.json "
                    "*.yaml *.yml *.sh *.sql",
                ),
                (
                    "All files",
                    "*.*",
                ),
            ],
        )

        if not path:
            return

        target = Path(
            path
        ).expanduser().resolve()

        if not target.is_file():
            return

        suffix = target.suffix.lower()

        image_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".bmp",
            ".gif",
        }

        document_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".ppt",
            ".pptx",
            ".txt",
            ".md",
        }

        spreadsheet_extensions = {
            ".xlsx",
            ".xls",
            ".csv",
            ".tsv",
        }

        database_extensions = {
            ".db",
            ".sqlite",
            ".sqlite3",
        }

        # ----------------------------------------------------
        # Canonical state
        # ----------------------------------------------------

        self.attached_file = str(target)
        self.attachment_name = target.name
        self.attachment_size = target.stat().st_size

        if suffix in image_extensions:
            kind = "image"
        elif suffix in document_extensions:
            kind = "document"
        elif suffix in spreadsheet_extensions:
            kind = "spreadsheet"
        elif suffix in database_extensions:
            kind = "database"
        else:
            kind = "file"

        self.attachment_kind = kind

        # ----------------------------------------------------
        # IMPORTANT:
        # Detach old CTkImage BEFORE replacing it.
        # Do not configure the label while the dead image is
        # still attached.
        # ----------------------------------------------------

        old_image = getattr(
            self,
            "attachment_thumbnail",
            None,
        )

        self.attachment_thumbnail = None

        try:
            self.attachment_preview.configure(
                image=None,
                text="",
            )
        except Exception as exc:
            print(
                "[ATTACHMENT PREVIEW RESET]",
                exc,
            )

        # Let Tk release the old image object naturally.
        del old_image

        # ----------------------------------------------------
        # Default icon
        # ----------------------------------------------------

        icons = {
            "image": "🖼",
            "document": "📄",
            "spreadsheet": "📊",
            "database": "🗄",
            "file": "📎",
        }

        backgrounds = {
            "image": "#e9f8ef",
            "document": "#fff4e5",
            "spreadsheet": "#eef9ee",
            "database": "#f1ecff",
            "file": "#eaf2ff",
        }

        self.attachment_preview.configure(
            image=None,
            text=icons[kind],
            fg_color=backgrounds[kind],
        )

        # ----------------------------------------------------
        # IMAGE THUMBNAIL
        # ----------------------------------------------------

        if (
            kind == "image"
            and Image is not None
        ):

            try:

                image = Image.open(
                    str(target)
                ).convert(
                    "RGB"
                )

                # Keep a real PIL copy alive for CTkImage.
                image.thumbnail(
                    (40, 40)
                )

                self.attachment_thumbnail = (
                    ctk.CTkImage(
                        light_image=image,
                        dark_image=image,
                        size=(40, 40),
                    )
                )

                self.attachment_preview.configure(
                    image=self.attachment_thumbnail,
                    text="",
                )

            except Exception as exc:

                print(
                    "[ATTACHMENT THUMBNAIL]",
                    exc,
                )

        # ----------------------------------------------------
        # FILE INFO
        # ----------------------------------------------------

        size = self.attachment_size

        if size >= 1024 * 1024:
            size_text = (
                f"{size / 1024 / 1024:.1f} MB"
            )
        elif size >= 1024:
            size_text = (
                f"{size / 1024:.0f} KB"
            )
        else:
            size_text = f"{size} B"

        self.file_label.configure(
            text=(
                target.name
                if len(target.name) <= 42
                else (
                    target.name[:34]
                    + "…"
                    + target.suffix
                )
            ),
        )

        self.file_meta.configure(
            text=(
                f"{kind.capitalize()} · "
                f"{size_text}"
            ),
        )

        # ----------------------------------------------------
        # SHOW CARD
        # ----------------------------------------------------

        self.attachment_card.grid()

        try:
            self.status_label.configure(
                text=(
                    f"Attached · "
                    f"{target.name}"
                ),
            )
        except Exception:
            pass

        print(
            "[ATTACHMENT READY]",
            f"path={self.attached_file}",
            f"kind={kind}",
            f"bytes={size}",
        )


    def clear_attachment(self):

        # ----------------------------------------------------
        # Remove image from widget FIRST.
        # Only then release the CTkImage reference.
        # This avoids dead pyimage references inside Tk.
        # ----------------------------------------------------

        preview = getattr(
            self,
            "attachment_preview",
            None,
        )

        if preview is not None:

            try:
                preview.configure(
                    image=None,
                    text="📎",
                    fg_color="#eaf2ff",
                )
            except Exception as exc:
                print(
                    "[ATTACHMENT CLEAR PREVIEW]",
                    exc,
                )

        self.attachment_thumbnail = None

        # ----------------------------------------------------
        # Canonical state
        # ----------------------------------------------------

        self.attached_file = None
        self.attachment_name = None
        self.attachment_kind = None
        self.attachment_size = 0

        # ----------------------------------------------------
        # Hide card
        # ----------------------------------------------------

        card = getattr(
            self,
            "attachment_card",
            None,
        )

        if card is not None:

            try:
                card.grid_remove()
            except Exception:
                pass

        # ----------------------------------------------------
        # Clear labels
        # ----------------------------------------------------

        label = getattr(
            self,
            "file_label",
            None,
        )

        if label is not None:
            try:
                label.configure(
                    text="",
                )
            except Exception:
                pass

        meta = getattr(
            self,
            "file_meta",
            None,
        )

        if meta is not None:
            try:
                meta.configure(
                    text="",
                )
            except Exception:
                pass

        try:
            self.status_label.configure(
                text="Local context ready",
            )
        except Exception:
            pass

        print(
            "[ATTACHMENT CLEARED]"
        )


    def build_prompt(
        self,
        question,
    ):

        uid = self.user.get(
            "user_id",
            self.user.get(
                "username",
                "local",
            ),
        )

        context = ""

        try:
            context = self.chat_service.context(
                self.chat_id,
                uid,
                10,
            )
        except Exception:
            context = ""

        prompt_parts = [
            "SYSTEM ROLE: Local AI Assistant.",
            "",
            "You are continuing an existing conversation.",
            "Use previous conversation only as context.",
            "Do NOT replay previous turns.",
            "Do NOT invent another user message.",
            "Do NOT invent another assistant response.",
            "Do NOT output USER: or ASSISTANT: labels.",
            "Do NOT emit model control tokens.",
            "Answer ONLY the current request.",
            "Complete the requested work when an action is requested.",
        ]

        if context:
            prompt_parts.extend([
                "",
                "PREVIOUS CONVERSATION:",
                "======================",
                context,
                "======================",
            ])

        prompt_parts.extend([
            "",
            "CURRENT USER REQUEST:",
            "=====================",
            str(question).strip(),
            "=====================",
            "",
            "RESPOND TO THE CURRENT REQUEST ONLY.",
        ])

        return "\n".join(
            prompt_parts
        )


    def send(self):

        if self.busy:
            return

        question = self.entry.get(
            "1.0",
            "end",
        ).strip()

        if not question:
            return

        self.entry.delete(
            "1.0",
            "end",
        )

        uid = self.user.get(
            "user_id",
            self.user.get(
                "username",
                "local",
            ),
        )

        # ====================================================
        # ACTUAL FILE EDIT ACTION
        # ====================================================

        file_edit_request = detect_file_edit_request(
            question
        )

        if file_edit_request:

            target = resolve_edit_target(
                question,
                self.last_created_file,
            )

            if target is None:
                # If there is no explicit file and no previous file,
                # ask only for the missing target.
                answer = (
                    "I need the file path to edit it."
                )

                self.add_message(
                    "LOCAL AI · FILE EDITOR",
                    answer,
                )

                self.chat_service.save_message(
                    self.chat_id,
                    uid,
                    "assistant",
                    answer,
                    "file_editor",
                )

                return

            self.busy = True

            self.send_button.configure(
                state="disabled",
                text="Editing…",
            )

            self.add_message(
                "LOCAL AI",
                (
                    "● FILE EDITOR · reading existing file…\n"
                    f"Target: {target}"
                ),
            )

            def edit_worker():

                try:

                    existing = target.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )

                    extension = target.suffix.lower()

                    mm = model_manager()

                    if mm is None:
                        raise RuntimeError(
                            "Coding model unavailable."
                        )

                    edit_prompt = (
                        "ROLE: FILE EDITOR.\n\n"
                        "You are editing an existing file.\n"
                        "The requested changes must be made to the "
                        "existing file, not merely explained.\n\n"
                        "STRICT OUTPUT RULES:\n"
                        "1. Return ONLY the complete replacement file.\n"
                        "2. Do not explain anything.\n"
                        "3. Do not say 'Sure'.\n"
                        "4. Do not say 'I can help'.\n"
                        "5. Do not say 'here is the code'.\n"
                        "6. Do not output 'Assistant:'.\n"
                        "7. Do not use markdown fences.\n"
                        "8. Do not output control tokens.\n"
                        "9. Preserve useful existing functionality unless "
                        "the user's request requires changing it.\n"
                        "10. The output will overwrite the existing file.\n\n"
                    )

                    if extension in (
                        ".html",
                        ".htm",
                    ):

                        edit_prompt += (
                            "HTML RULES:\n"
                            "Return one complete HTML document.\n"
                            "Start with <!DOCTYPE html>.\n"
                            "End with </html>.\n"
                            "Implement the requested Three.js animation "
                            "directly in the HTML.\n"
                            "Do not create a separate JS file unless the "
                            "user explicitly requests one.\n"
                            "Do not use placeholder comments like "
                            "'Your code here'.\n\n"
                        )

                    edit_prompt += (
                        "USER EDIT REQUEST:\n"
                        f"{question}\n\n"
                        "EXISTING FILE CONTENT:\n"
                        "----------------------\n"
                        f"{existing}\n"
                        "----------------------\n\n"
                        "Return ONLY the complete updated file."
                    )

                    result = mm.run_worker(
                        worker_type="coding",
                        prompt=edit_prompt,
                        request_id=uuid.uuid4().hex,
                        max_tokens=5000,
                    )

                    raw = getattr(
                        result,
                        "content",
                        "",
                    )

                    content = clean_edited_content(
                        raw,
                        extension,
                    )

                    if not content:
                        raise RuntimeError(
                            "Coding model returned empty file content."
                        )

                    written = write_verified_file(
                        target,
                        content,
                    )

                    self.last_created_file = str(
                        written
                    )

                    answer = (
                        "Done — I edited the existing file "
                        "and saved the changes.\n\n"
                        f"Path: {written}\n"
                        f"Size: {written.stat().st_size} bytes"
                    )

                    self.after(
                        0,
                        lambda answer=answer:
                        self._finish_request(
                            uid,
                            answer,
                            "coding + file editor",
                        ),
                    )

                except Exception as exc:

                    error = str(exc)

                    self.after(
                        0,
                        lambda error=error:
                        self._finish_request(
                            uid,
                            (
                                "I could not complete the file edit.\n\n"
                                f"Reason: {error}"
                            ),
                            "file editor",
                        ),
                    )

            threading.Thread(
                target=edit_worker,
                daemon=True,
            ).start()

            return


        # ----------------------------------------------------
        # SAVE USER MESSAGE
        # ----------------------------------------------------

        self.chat_service.save_message(
            self.chat_id,
            uid,
            "user",
            question,
            "user",
        )

        self.add_message(
            "YOU",
            question,
        )

        # ====================================================
        # FILE GENERATION IS AN ACTION, NOT NORMAL CHAT
        # ====================================================

        file_request = detect_file_request(
            question
        )

        if file_request:

            self.busy = True

            self.send_button.configure(
                state="disabled",
                text="Generating…",
            )

            target = file_request["target"]
            extension = file_request["extension"]

            self.add_message(
                "LOCAL AI",
                (
                    "● FILE AGENT · generating…\n"
                    f"Target: {target}"
                ),
            )

            def file_generation_worker():

                try:

                    mm = model_manager()

                    if mm is None:
                        raise RuntimeError(
                            "Coding model is unavailable."
                        )

                    # IMPORTANT:
                    # This is NOT a conversational prompt.
                    # The result is going directly into a file.
                    prompt = (
                        "FILE GENERATION MODE.\n\n"
                        "You are a deterministic file-content generator.\n"
                        f"Target type: {extension}\n\n"
                        "RULES:\n"
                        "Return ONLY the complete raw contents of the file.\n"
                        "Do not write explanations.\n"
                        "Do not say hello.\n"
                        "Do not say 'Sure'.\n"
                        "Do not say 'I can help'.\n"
                        "Do not say 'Here is the code'.\n"
                        "Do not write 'Assistant:'.\n"
                        "Do not use markdown fences.\n"
                        "Do not emit model control tokens.\n"
                        "Do not tell the user to save or run the file.\n"
                        "Actually generate the complete requested file.\n\n"
                    )

                    # Specific HTML guidance.
                    if extension == ".html":

                        prompt += (
                            "HTML REQUIREMENTS:\n"
                            "Return one complete HTML document.\n"
                            "Start with <!DOCTYPE html>.\n"
                            "End with </html>.\n"
                            "If Three.js is requested, implement the "
                            "actual 3D scene and animation.\n"
                            "Do not return a placeholder saying "
                            "'Your code here'.\n"
                            "Do not explain how to expand it later.\n\n"
                        )

                    prompt += (
                        "USER REQUEST:\n"
                        f"{question}\n\n"
                        "OUTPUT ONLY THE COMPLETE FILE CONTENT."
                    )

                    result = mm.run_worker(
                        worker_type="coding",
                        prompt=prompt,
                        request_id=uuid.uuid4().hex,
                        max_tokens=3000,
                    )

                    raw = getattr(
                        result,
                        "content",
                        "",
                    )

                    content = clean_file_content(
                        raw,
                        extension,
                    )

                    if not content:
                        raise RuntimeError(
                            "Coding model returned no file content."
                        )

                    written = write_verified_file(
                        target,
                        content,
                    )

                    self.last_created_file = str(
                        written
                    )

                    answer = (
                        "Done — the AI generated the file and "
                        "actually created it on the local machine.\n\n"
                        f"Path: {written}\n"
                        f"Size: {written.stat().st_size} bytes"
                    )

                    self.after(
                        0,
                        lambda answer=answer:
                        self._finish_request(
                            uid,
                            answer,
                            "coding + file agent",
                        ),
                    )

                except Exception as exc:

                    error = str(exc)

                    self.after(
                        0,
                        lambda error=error:
                        self._finish_request(
                            uid,
                            (
                                "The file-generation action failed.\n\n"
                                f"Reason: {error}"
                            ),
                            "file agent",
                        ),
                    )

            threading.Thread(
                target=file_generation_worker,
                daemon=True,
            ).start()

            return


        # ----------------------------------------------------
        # REAL FILE GENERATION REQUEST
        # ----------------------------------------------------

        # ----------------------------------------------------
        # NORMAL AI ROUTING
        # ----------------------------------------------------

        has_file = bool(
            self.attached_file
        )

        context = ""

        try:
            context = self.chat_service.context(
                self.chat_id,
                uid,
                12,
            )
        except Exception:
            pass

        intent = self.semantic_organizer.organize(
            question,
            context=context,
            state=self.conversation_state,
            has_attachment=bool(
                self.attached_file
            ),
        )

        selected = self.mode.get().strip().lower()

        # An explicit file-generation request is always an action,
        # regardless of the selected model mode.
        if file_request:
            selected = "auto"

        if selected in (
            "",
            "auto",
        ):
            intent = detect_intent(
                question,
                has_file,
            )
        else:
            intent = selected

        # Sensitive operations remain guarded.
        if risky(question):
            intent = "workflow"

        self.add_message(
            "LOCAL AI",
            f"● {intent.upper()} · working…",
        )

        self.busy = True

        self.send_button.configure(
            state="disabled",
            text="Working…",
        )

        prompt = self.build_prompt(
            question
        )

        def run():

            try:

                # --------------------------------------------
                # VISION
                # --------------------------------------------

                if intent == "vision":

                    mm = model_manager()

                    if mm is None:
                        raise RuntimeError(
                            "Vision Model Manager unavailable."
                        )

                    if not self.attached_file:
                        raise ValueError(
                            "An image is required."
                        )

                    result = mm.run_worker(
                        worker_type="vision",
                        prompt=(
                            "Analyze the attached image carefully. "
                            "Answer the user's request directly. "
                            "Identify visible objects, text, labels, "
                            "layout, and relevant visual details. "
                            "Do not invent details that are not visible. "
                            "Provide a useful answer even for short "
                            "requests such as 'identify' or 'what is it'. "
                            "\n\nUSER REQUEST:\n"
                            + question
                        ),
                        image_path=self.attached_file,
                        request_id=uuid.uuid4().hex,
                        max_tokens=2200,
                    )

                    answer = clean_ai_output(
                        getattr(
                            result,
                            "content",
                            "",
                        )
                    )

                    model_name = "vision"

                # --------------------------------------------
                # DOCUMENT
                # --------------------------------------------

                elif intent == "document":

                    mm = model_manager()

                    if mm is None:
                        raise RuntimeError(
                            "Document model unavailable."
                        )

                    result = mm.run_worker(
                        worker_type="general",
                        prompt=prompt,
                        request_id=uuid.uuid4().hex,
                        max_tokens=2200,
                    )

                    answer = clean_ai_output(
                        getattr(
                            result,
                            "content",
                            "",
                        )
                    )

                    model_name = "document"

                # --------------------------------------------
                # CODING
                # --------------------------------------------

                elif intent == "coding":

                    mm = model_manager()

                    if mm is None:
                        raise RuntimeError(
                            "Coding model unavailable."
                        )

                    coding_prompt = (
                        "You are the local coding assistant.\n"
                        "Complete the user's request directly and provide a comprehensive, detailed explanation of the solution.\n"
                        "Do not give short answers; instead, provide a well-structured, lengthy, and highly conversational response.\n"
                        "Return working code when requested, along with clear documentation and step-by-step reasoning.\n"
                        "Do not say you will do it later.\n"
                        "Do not prefix with 'Assistant:'.\n"
                        "Do not emit <|im_end|>.\n\n"
                        + prompt
                    )

                    result = mm.run_worker(
                        worker_type="coding",
                        prompt=coding_prompt,
                        request_id=uuid.uuid4().hex,
                        max_tokens=1400,
                    )

                    answer = clean_ai_output(
                        getattr(
                            result,
                            "content",
                            "",
                        )
                    )

                    model_name = "coding"

                # --------------------------------------------
                # WORKFLOW
                # --------------------------------------------

                elif intent == "workflow":

                    if WORKFLOW_ENGINE is None:
                        raise RuntimeError(
                            "Workflow Engine unavailable."
                        )

                    state = (
                        WORKFLOW_ENGINE.execute_workflow(
                            task_description=question,
                            user_id=uid,
                            role=self.user.get(
                                "role",
                                "GRADE_2",
                            ),
                            session_id=uuid.uuid4().hex,
                        )
                    )

                    answer = clean_ai_output(
                        getattr(
                            state,
                            "final_response",
                            "",
                        )
                    )

                    model_name = "workflow"

                # --------------------------------------------
                # GENERAL
                # --------------------------------------------

                else:

                    mm = model_manager()

                    if mm is None:
                        raise RuntimeError(
                            "General model unavailable."
                        )

                    general_prompt = (
                        "You are the local General AI assistant.\n"
                        "Answer the current request comprehensively, providing a highly detailed, lengthy, and conversational response.\n"
                        "Do not give short answers. Be descriptive, polite, and explain your reasoning fully.\n"
                        "Use conversation context when useful.\n"
                        "Complete the requested work before returning.\n"
                        "Do not emit Assistant: prefixes.\n"
                        "Do not emit model control tokens.\n\n"
                        + prompt
                    )

                    result = mm.run_worker(
                        worker_type="general",
                        prompt=general_prompt,
                        request_id=uuid.uuid4().hex,
                        max_tokens=2200,
                    )

                    answer = clean_ai_output(
                        getattr(
                            result,
                            "content",
                            "",
                        )
                    )

                    model_name = "general"

                self.after(
                    0,
                    lambda:
                    self._finish_request(
                        uid,
                        answer,
                        model_name,
                    ),
                )

            except Exception as exc:

                error = str(exc)

                self.after(
                    0,
                    lambda error=error:
                    self._finish_request(
                        uid,
                        f"Error: {error}",
                        "error",
                    ),
                )

        threading.Thread(
            target=run,
            daemon=True,
        ).start()


    def _finish_request(
        self,
        uid,
        answer,
        model_name,
    ):

        self.add_message(
            f"LOCAL AI · {model_name.upper()}",
            answer,
        )

        self.chat_service.save_message(
            self.chat_id,
            uid,
            "assistant",
            answer,
            model_name,
        )

        self.refresh_chat_list()

        self.busy = False

        self.send_button.configure(
            state="normal",
            text="Send",
        )


    def show_files(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        ctk.CTkLabel(
            page,
            text="Files",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(
            anchor="w",
        )

        entry = ctk.CTkEntry(
            page,
            height=38,
        )

        entry.insert(
            0,
            str(ROOT),
        )

        entry.pack(
            fill="x",
            pady=12,
        )

        box = ctk.CTkTextbox(
            page,
            fg_color="#ffffff",
            text_color="#17202a",
        )

        box.pack(
            fill="both",
            expand=True,
        )

        def browse():
            try:
                path = Path(
                    entry.get()
                ).expanduser().resolve()

                box.delete(
                    "1.0",
                    "end",
                )

                for p in sorted(
                    path.iterdir(),
                    key=lambda x: (
                        not x.is_dir(),
                        x.name.lower(),
                    ),
                ):
                    box.insert(
                        "end",
                        (
                            ("📁 " if p.is_dir() else "📄 ")
                            + p.name
                            + "\n"
                        ),
                    )

            except Exception as exc:
                box.insert(
                    "end",
                    f"ERROR: {exc}",
                )

        ctk.CTkButton(
            page,
            text="OPEN",
            command=browse,
        ).pack(
            anchor="e",
            pady=10,
        )

        browse()

    def show_workflow(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        ctk.CTkLabel(
            page,
            text="Workflow",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(anchor="w")

        box = ctk.CTkTextbox(
            page,
            fg_color="#ffffff",
            text_color="#17202a",
        )

        box.pack(
            fill="both",
            expand=True,
            pady=12,
        )

        if self.current_state is None:
            box.insert(
                "end",
                "No workflow executed in this session.",
            )
        else:
            state = self.current_state
            box.insert(
                "end",
                f"STATUS: {getattr(state, 'status', 'UNKNOWN')}\n"
                f"COMPLETED: {getattr(state, 'completed_steps', [])}\n"
                f"FAILED: {getattr(state, 'failed_steps', [])}\n"
                f"VERIFICATION: {getattr(state, 'verification_summary', {})}\n",
            )

    def show_models(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        ctk.CTkLabel(
            page,
            text="Models",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(anchor="w")

        box = ctk.CTkTextbox(
            page,
            fg_color="#ffffff",
            text_color="#17202a",
        )

        box.pack(
            fill="both",
            expand=True,
            pady=12,
        )

        mm = model_manager()

        for worker in [
            "organizer",
            "general",
            "coding",
            "vision",
            "document",
        ]:

            try:
                state = (
                    mm.get_model_state(worker)
                    if mm
                    else "UNAVAILABLE"
                )
            except Exception as exc:
                state = f"ERROR: {exc}"

            box.insert(
                "end",
                f"{worker.upper():12} {state}\n",
            )

    def show_employees(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        ctk.CTkLabel(
            page,
            text="Employees",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(anchor="w")

        if str(
            self.user.get(
                "role",
                "",
            )
        ).upper() != "ADMIN":

            ctk.CTkLabel(
                page,
                text="ADMIN access required.",
                text_color="#c43d49",
            ).pack(
                anchor="w",
                pady=12,
            )

            return

        form = ctk.CTkFrame(
            page,
            fg_color="#ffffff",
            corner_radius=12,
        )

        form.pack(
            fill="x",
            pady=12,
        )

        name = ctk.CTkEntry(
            form,
            placeholder_text="Full name",
        )
        name.pack(
            fill="x",
            padx=12,
            pady=6,
        )

        username = ctk.CTkEntry(
            form,
            placeholder_text="Username",
        )
        username.pack(
            fill="x",
            padx=12,
            pady=6,
        )

        password = ctk.CTkEntry(
            form,
            placeholder_text="Password",
            show="•",
        )
        password.pack(
            fill="x",
            padx=12,
            pady=6,
        )

        department = ctk.CTkEntry(
            form,
            placeholder_text="Department",
        )
        department.pack(
            fill="x",
            padx=12,
            pady=6,
        )

        role = ctk.CTkOptionMenu(
            form,
            values=[
                "GRADE_1",
                "GRADE_2",
                "GRADE_3",
                "ADMIN",
            ],
        )
        role.pack(
            padx=12,
            pady=6,
        )

        result = ctk.CTkLabel(
            form,
            text="",
        )
        result.pack(
            anchor="w",
            padx=12,
        )

        def create():

            if AuthService is None:
                result.configure(
                    text="Auth service unavailable.",
                    text_color="#c43d49",
                )
                return

            try:

                user = AuthService().create_user(
                    username=username.get().strip(),
                    password=password.get(),
                    full_name=name.get().strip(),
                    department=department.get().strip(),
                    role=role.get(),
                    operator_user_id=self.user.get(
                        "user_id"
                    ),
                )

                result.configure(
                    text=f"Created {user.get('username')}",
                    text_color="#16875a",
                )

            except Exception as exc:
                result.configure(
                    text=str(exc),
                    text_color="#c43d49",
                )

        ctk.CTkButton(
            form,
            text="CREATE EMPLOYEE",
            command=create,
        ).pack(
            anchor="e",
            padx=12,
            pady=12,
        )

    def show_audit(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        ctk.CTkLabel(
            page,
            text="Audit",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(anchor="w")

        box = ctk.CTkTextbox(
            page,
            fg_color="#ffffff",
            text_color="#17202a",
        )

        box.pack(
            fill="both",
            expand=True,
            pady=12,
        )

        if AUDIT is None:
            box.insert(
                "end",
                "Audit service unavailable.",
            )
            return

        try:
            result = AUDIT.verify_integrity()

            box.insert(
                "end",
                f"CHAIN VALID: {result.get('chain_valid')}\n"
                f"VERIFIED: {result.get('verified')}\n"
                f"RECORDS: {result.get('total_records_checked', 0)}\n",
            )

        except Exception as exc:
            box.insert(
                "end",
                f"AUDIT ERROR: {exc}",
            )

    def show_ide(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        ctk.CTkLabel(
            page,
            text="IDE",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(
            anchor="w",
        )

        ctk.CTkLabel(
            page,
            text=(
                "Agentic development environment "
                "runs in a dedicated process."
            ),
            text_color="#77818d",
        ).pack(
            anchor="w",
            pady=(4, 12),
        )

        status = ctk.CTkLabel(
            page,
            text="Ready to launch IDE",
            text_color="#77818d",
        )

        status.pack(
            anchor="w",
            pady=8,
        )

        def launch():

            try:

                import os
                import sys
                import subprocess

                env = os.environ.copy()

                env[
                    "PYTHONUNBUFFERED"
                ] = "1"

                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "desktop_gui.agentic_ide",
                    ],
                    cwd=str(ROOT),
                    env=env,
                    start_new_session=True,
                )

                status.configure(
                    text="IDE launched",
                    text_color="#16875a",
                )

            except Exception as exc:

                status.configure(
                    text=f"IDE launch failed: {exc}",
                    text_color="#c43d49",
                )

        ctk.CTkButton(
            page,
            text="OPEN AGENTIC IDE",
            width=180,
            height=42,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=launch,
        ).pack(
            anchor="w",
            pady=12,
        )


    def show_sandbox(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        page.grid_columnconfigure(
            0,
            weight=1,
        )

        page.grid_rowconfigure(
            2,
            weight=1,
        )

        ctk.CTkLabel(
            page,
            text="Sandbox",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ctk.CTkLabel(
            page,
            text=(
                "Local execution workspace · "
                "network disabled by policy"
            ),
            text_color="#718096",
        ).grid(
            row=0,
            column=0,
            sticky="e",
        )

        controls = ctk.CTkFrame(
            page,
            fg_color="#ffffff",
            corner_radius=12,
        )

        controls.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=12,
        )

        ctk.CTkLabel(
            controls,
            text="Language",
            text_color="#334155",
            font=ctk.CTkFont(
                size=11,
                weight="bold",
            ),
        ).pack(
            side="left",
            padx=(12, 8),
            pady=10,
        )

        language_values = [
            x["label"]
            + (
                " ✓"
                if x["available"]
                else " · unavailable"
            )
            for x in available_languages()
        ]

        self.sandbox_language_menu = ctk.CTkOptionMenu(
            controls,
            values=language_values,
            width=190,
            command=self._sandbox_language_changed,
        )

        self.sandbox_language_menu.pack(
            side="left",
            pady=8,
        )

        self.sandbox_editor = ctk.CTkTextbox(
            page,
            fg_color="#111827",
            text_color="#e5eefc",
            font=(
                "DejaVu Sans Mono",
                11,
            ),
        )

        self.sandbox_editor.grid(
            row=2,
            column=0,
            sticky="nsew",
            pady=(0, 10),
        )

        self.sandbox_output = ctk.CTkTextbox(
            page,
            height=170,
            fg_color="#0b1220",
            text_color="#b8c7da",
            font=(
                "DejaVu Sans Mono",
                10,
            ),
        )

        self.sandbox_output.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )

        run_button = ctk.CTkButton(
            controls,
            text="▶ Run locally",
            width=130,
            command=self.run_sandbox_code,
        )

        run_button.pack(
            side="left",
            padx=12,
        )

        self.sandbox_status = ctk.CTkLabel(
            controls,
            text="Ready",
            text_color="#16a34a",
        )

        self.sandbox_status.pack(
            side="left",
            padx=6,
        )

        self.sandbox_language_menu.set(
            "Python ✓"
            if "Python ✓" in language_values
            else language_values[0]
        )

    def _sandbox_language_changed(
        self,
        value,
    ):

        self.sandbox_language = (
            value.split(" ·")[0]
            .replace(" ✓", "")
            .strip()
            .lower()
        )

        self.sandbox_status.configure(
            text=f"Selected: {value}",
            text_color="#475569",
        )

    def run_sandbox_code(self):

        language = (
            self.sandbox_language
        )

        spec = next(
            (
                x
                for x in available_languages()
                if x["label"].lower()
                == language
            ),
            None,
        )

        if spec is None or not spec["available"]:

            self.sandbox_status.configure(
                text="Runtime unavailable",
                text_color="#dc2626",
            )

            return

        code = self.sandbox_editor.get(
            "1.0",
            "end",
        ).strip()

        if not code:
            return

        self.sandbox_output.delete(
            "1.0",
            "end",
        )

        self.sandbox_output.insert(
            "end",
            "Running...\n",
        )

        self.sandbox_status.configure(
            text=f"Running {spec['label']}...",
            text_color="#2563eb",
        )

        # Actual sandbox execution is delegated to the existing
        # sandbox service rather than executing arbitrary shell
        # commands from the GUI.
        try:

            from tools.sandbox.sandbox_runner import (
                SANDBOX_RUNNER,
            )

            result = SANDBOX_RUNNER.run(
                code=code,
                language=spec["key"],
                timeout=30,
            )

            self.sandbox_output.delete(
                "1.0",
                "end",
            )

            self.sandbox_output.insert(
                "end",
                (
                    f"EXIT: {result.get('exit_code')}\n\n"
                    f"STDOUT:\n{result.get('stdout', '')}\n\n"
                    f"STDERR:\n{result.get('stderr', '')}"
                ),
            )

            self.sandbox_status.configure(
                text="Completed",
                text_color="#16a34a"
                if result.get("exit_code") == 0
                else "#dc2626",
            )

        except Exception as exc:

            self.sandbox_output.delete(
                "1.0",
                "end",
            )

            self.sandbox_output.insert(
                "end",
                str(exc),
            )

            self.sandbox_status.configure(
                text="Failed",
                text_color="#dc2626",
            )


    def _sandbox_language_changed(
        self,
        value,
    ):

        self.sandbox_language = (
            value.split(" ·")[0]
            .replace(" ✓", "")
            .strip()
            .lower()
        )

        self.sandbox_status.configure(
            text=f"Selected: {value}",
            text_color="#475569",
        )

    def run_sandbox_code(self):

        language = (
            self.sandbox_language
        )

        spec = next(
            (
                x
                for x in available_languages()
                if x["label"].lower()
                == language
            ),
            None,
        )

        if spec is None or not spec["available"]:

            self.sandbox_status.configure(
                text="Runtime unavailable",
                text_color="#dc2626",
            )

            return

        code = self.sandbox_editor.get(
            "1.0",
            "end",
        ).strip()

        if not code:
            return

        self.sandbox_output.delete(
            "1.0",
            "end",
        )

        self.sandbox_output.insert(
            "end",
            "Running...\n",
        )

        self.sandbox_status.configure(
            text=f"Running {spec['label']}...",
            text_color="#2563eb",
        )

        # Actual sandbox execution is delegated to the existing
        # sandbox service rather than executing arbitrary shell
        # commands from the GUI.
        try:

            from tools.sandbox.sandbox_runner import (
                SANDBOX_RUNNER,
            )

            result = SANDBOX_RUNNER.run(
                code=code,
                language=spec["key"],
                timeout=30,
            )

            self.sandbox_output.delete(
                "1.0",
                "end",
            )

            self.sandbox_output.insert(
                "end",
                (
                    f"EXIT: {result.get('exit_code')}\n\n"
                    f"STDOUT:\n{result.get('stdout', '')}\n\n"
                    f"STDERR:\n{result.get('stderr', '')}"
                ),
            )

            self.sandbox_status.configure(
                text="Completed",
                text_color="#16a34a"
                if result.get("exit_code") == 0
                else "#dc2626",
            )

        except Exception as exc:

            self.sandbox_output.delete(
                "1.0",
                "end",
            )

            self.sandbox_output.insert(
                "end",
                str(exc),
            )

            self.sandbox_status.configure(
                text="Failed",
                text_color="#dc2626",
            )


    def show_tools(self):

        self.clear_page()

        page = ctk.CTkFrame(
            self.main,
            fg_color="#f5f7fa",
        )

        page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        ctk.CTkLabel(
            page,
            text="Tools",
            text_color="#17202a",
            font=ctk.CTkFont(
                size=23,
                weight="bold",
            ),
        ).pack(anchor="w")

        cwd = ctk.CTkEntry(
            page,
            height=38,
        )

        cwd.insert(
            0,
            str(ROOT),
        )

        cwd.pack(
            fill="x",
            pady=8,
        )

        cmd = ctk.CTkEntry(
            page,
            height=38,
            placeholder_text="python3 --version",
        )

        cmd.pack(
            fill="x",
            pady=8,
        )

        output = ctk.CTkTextbox(
            page,
            fg_color="#ffffff",
            text_color="#17202a",
        )

        output.pack(
            fill="both",
            expand=True,
            pady=8,
        )

        def execute():

            rc, stdout, stderr = safe_command(
                cmd.get(),
                cwd.get(),
            )

            output.insert(
                "end",
                f"$ {cmd.get()}\n"
                f"{stdout}\n"
                f"{stderr}\n"
                f"[exit {rc}]\n\n",
            )

            output.see("end")

        ctk.CTkButton(
            page,
            text="RUN",
            command=execute,
        ).pack(
            anchor="e",
        )


class App(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title(
            "Sovereign Industrial AI Workbench"
        )

        self.geometry(
            "1400x850"
        )

        self.minsize(
            1050,
            700,
        )

        self.configure(
            fg_color="#f5f7fa"
        )

        ensure_db()
        ensure_sandbox()

        if DEV_AUTH_BYPASS:
            self.show_workbench(DEV_USER)
        else:
            self.show_login()

    def show_login(self):

        for child in self.winfo_children():
            child.destroy()

        login = Login(
            self,
            self.show_workbench,
        )

        login.pack(
            fill="both",
            expand=True,
        )

    def show_workbench(self, user):

        for child in self.winfo_children():
            child.destroy()

        workbench = Workbench(
            self,
            user,
        )

        workbench.pack(
            fill="both",
            expand=True,
        )


def main():

    ctk.set_appearance_mode(
        "light"
    )

    ctk.set_default_color_theme(
        "blue"
    )

    app = App()

    app.mainloop()


if __name__ == "__main__":
    main()
