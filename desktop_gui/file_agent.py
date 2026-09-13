from __future__ import annotations

import re
from pathlib import Path


def write_verified_file(
    path,
    content,
    *,
    overwrite: bool = False,
) -> str:
    """
    Write an artifact and verify that it was actually written.

    Returns the final absolute path.

    By default this function never silently overwrites an
    existing artifact.
    """

    target = Path(
        path
    ).expanduser().resolve()

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if target.exists() and not overwrite:
        target = unique_path(
            target
        )

    data = str(
        content or ""
    )

    if not data.strip():
        raise ValueError(
            "Refusing to write an empty artifact."
        )

    # Atomic-ish write through a temporary sibling.
    temp = target.with_name(
        target.name + ".tmp"
    )

    try:

        temp.write_text(
            data,
            encoding="utf-8",
        )

        if not temp.exists():
            raise RuntimeError(
                "Temporary artifact was not created."
            )

        if temp.stat().st_size == 0:
            raise RuntimeError(
                "Temporary artifact is empty."
            )

        temp.replace(
            target
        )

    finally:

        if temp.exists():
            try:
                temp.unlink()
            except Exception:
                pass

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    if not target.exists():
        raise RuntimeError(
            f"Artifact was not created: {target}"
        )

    if not target.is_file():
        raise RuntimeError(
            f"Artifact is not a regular file: {target}"
        )

    size = target.stat().st_size

    if size <= 0:
        raise RuntimeError(
            f"Artifact is empty: {target}"
        )

    # Basic format verification.
    suffix = target.suffix.lower()

    if suffix in {
        ".html",
        ".htm",
    }:

        written = target.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if "<html" not in written.lower():
            raise RuntimeError(
                "HTML verification failed: <html> not found."
            )

        if "</html>" not in written.lower():
            raise RuntimeError(
                "HTML verification failed: </html> not found."
            )

    elif suffix == ".py":

        written = target.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if not written.strip():
            raise RuntimeError(
                "Python verification failed: empty source."
            )

    return str(target)


def unique_path(path: Path) -> Path:
    """
    Never silently overwrite an existing generated artifact.
    """

    path = path.expanduser().resolve()

    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    i = 1

    while True:
        candidate = parent / f"{stem}_{i}{suffix}"

        if not candidate.exists():
            return candidate

        i += 1


def infer_extension(
    text: str,
    fallback: str = ".html",
) -> str:

    q = str(text or "").lower()

    # Three.js / webpage => HTML
    if any(
        x in q
        for x in (
            "three.js",
            "three js",
            "threejs",
            "webpage",
            "web page",
            "html",
        )
    ):
        return ".html"

    if "python" in q or ".py" in q:
        return ".py"

    if "javascript" in q or ".js" in q:
        return ".js"

    if "css" in q or ".css" in q:
        return ".css"

    if "json" in q or ".json" in q:
        return ".json"

    if "markdown" in q or ".md" in q:
        return ".md"

    return fallback


def infer_directory(
    text: str,
    fallback: Path | None = None,
) -> Path:

    q = str(text or "").lower()

    if "downloads" in q or "download" in q:
        return Path.home() / "Downloads"

    if "desktop" in q:
        return Path.home() / "Desktop"

    if "documents" in q:
        return Path.home() / "Documents"

    if (
        "home directory" in q
        or "home folder" in q
        or "in home" in q
        or "home" == q.strip()
    ):
        return Path.home()

    if fallback is not None:
        return fallback.expanduser().resolve()

    return Path.home()


def infer_filename(
    text: str,
    extension: str,
) -> str:

    for pattern in (
        r"(?:named|called)\s+([A-Za-z0-9_.-]+)",
        r"\b([A-Za-z0-9_.-]+\.(?:html?|py|js|css|json|md|txt|csv|yaml|yml))\b",
    ):

        match = re.search(
            pattern,
            text or "",
            re.I,
        )

        if match:

            candidate = Path(
                match.group(1)
            ).name

            if candidate.lower() not in {
                "home",
                "downloads",
                "desktop",
                "documents",
                "file",
                "folder",
                "directory",
            }:
                return candidate

    defaults = {
        ".html": "generated_page.html",
        ".py": "generated_script.py",
        ".js": "generated_script.js",
        ".css": "generated_style.css",
        ".json": "generated_data.json",
        ".md": "generated_note.md",
        ".txt": "generated_file.txt",
    }

    return defaults.get(
        extension,
        "generated_file" + extension,
    )


def detect_generation(
    request: str,
    *,
    previous_intent: str | None = None,
    previous_file: str | None = None,
    previous_directory: str | None = None,
):
    q = " ".join(
        str(request or "").lower().split()
    )

    # --------------------------------------------------------
    # Explicit create/generate
    # --------------------------------------------------------

    explicit = any(
        x in q
        for x in (
            "generate",
            "create",
            "make",
            "build",
            "write",
            "save",
            "bana",
            "banao",
        )
    )

    # --------------------------------------------------------
    # Short continuation
    # --------------------------------------------------------

    continuation = (
        previous_intent == "CREATE_FILE"
        and (
            "webpage" in q
            or "web page" in q
            or "ui" in q
            or "html" in q
            or "python" in q
            or "py" in q
            or "css" in q
            or "javascript" in q
            or "js" in q
        )
    )

    # --------------------------------------------------------
    # Explicit file language
    # --------------------------------------------------------

    file_signal = any(
        x in q
        for x in (
            "file",
            "webpage",
            "web page",
            ".html",
            ".py",
            ".js",
            ".css",
            ".json",
            "python file",
            "html file",
        )
    )

    if not (
        (explicit and file_signal)
        or continuation
    ):
        return None

    extension = infer_extension(
        request
    )

    previous_dir = (
        Path(previous_directory)
        if previous_directory
        else None
    )

    directory = infer_directory(
        request,
        fallback=previous_dir,
    )

    filename = infer_filename(
        request,
        extension,
    )

    target = (
        directory / filename
    ).resolve()

    return {
        "extension": extension,
        "directory": directory,
        "filename": filename,
        "target": target,
        "previous_file": previous_file,
    }


def clean_generated_content(
    raw: str,
    extension: str,
) -> str:

    text = str(
        raw or ""
    ).replace(
        "\r\n",
        "\n",
    ).strip()

    for token in (
        "<|im_end|>",
        "<|im_start|>",
        "<|endoftext|>",
        "<|eot_id|>",
        "<|start_header_id|>",
        "<|end_header_id|>",
    ):
        text = text.replace(
            token,
            "",
        )

    ext = extension.lower()

    # ========================================================
    # HTML
    # ========================================================

    if ext == ".html":

        start = re.search(
            r"<!DOCTYPE\s+html\b",
            text,
            re.I,
        )

        if not start:
            start = re.search(
                r"<html\b",
                text,
                re.I,
            )

        if start:

            text = text[
                start.start():
            ]

            end = re.search(
                r"</html\s*>",
                text,
                re.I,
            )

            if end:

                return text[
                    :end.end()
                ].strip()

        raise ValueError(
            "No complete HTML document found."
        )

    # ========================================================
    # Generic code
    # ========================================================

    text = re.sub(
        r"^\s*Assistant\s*:\s*",
        "",
        text,
        count=1,
        flags=re.I,
    )

    # Stop repeated Assistant loops.
    match = re.search(
        r"\n\s*Assistant\s*:",
        text,
        re.I,
    )

    if match:
        text = text[:match.start()]

    fence = re.match(
        r"^\s*```[A-Za-z0-9_+-]*\s*\n?"
        r"([\s\S]*?)"
        r"\n?```\s*$",
        text,
        re.I,
    )

    if fence:
        text = fence.group(1)

    return text.strip()


def basic_fallback(
    extension: str,
    request: str = "",
) -> str:

    ext = extension.lower()
    q = str(request or "").lower()

    if ext == ".html":

        if (
            "three" in q
            or "3d" in q
            or "animation" in q
        ):

            return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Three.js 3D Experience</title>
<style>
:root {
    color-scheme: dark;
    font-family: Inter, system-ui, sans-serif;
}
html, body {
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #070b14;
}
canvas {
    display: block;
}
.overlay {
    position: fixed;
    inset: 24px auto auto 24px;
    z-index: 5;
    padding: 20px 24px;
    border-radius: 16px;
    background: rgba(15, 23, 42, .72);
    border: 1px solid rgba(255,255,255,.12);
    backdrop-filter: blur(16px);
    color: white;
}
.overlay h1 {
    margin: 0 0 6px;
    font-size: 22px;
}
.overlay p {
    margin: 0;
    opacity: .7;
}
</style>
</head>
<body>

<div class="overlay">
    <h1>Three.js Experience</h1>
    <p>Generated locally by Sovereign AI</p>
</div>

<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script>
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x070b14);

const camera = new THREE.PerspectiveCamera(
    60,
    innerWidth / innerHeight,
    0.1,
    100
);
camera.position.z = 4.5;

const renderer = new THREE.WebGLRenderer({
    antialias: true
});
renderer.setPixelRatio(
    Math.min(devicePixelRatio, 2)
);
renderer.setSize(
    innerWidth,
    innerHeight
);
document.body.appendChild(
    renderer.domElement
);

scene.add(
    new THREE.AmbientLight(
        0xffffff,
        1.2
    )
);

const light = new THREE.PointLight(
    0x7aa2ff,
    3
);
light.position.set(3, 3, 4);
scene.add(light);

const geometry =
    new THREE.IcosahedronGeometry(
        1.15,
        3
    );

const material =
    new THREE.MeshStandardMaterial({
        color: 0x4f8cff,
        metalness: .5,
        roughness: .22
    });

const mesh =
    new THREE.Mesh(
        geometry,
        material
    );

scene.add(mesh);

function animate(time) {

    requestAnimationFrame(
        animate
    );

    mesh.rotation.x =
        time * .00028;

    mesh.rotation.y =
        time * .0004;

    renderer.render(
        scene,
        camera
    );
}

animate(0);

addEventListener(
    "resize",
    () => {
        camera.aspect =
            innerWidth / innerHeight;

        camera.updateProjectionMatrix();

        renderer.setSize(
            innerWidth,
            innerHeight
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
<title>Generated Webpage</title>
<style>
body {
    margin: 0;
    min-height: 100vh;
    display: grid;
    place-items: center;
    background: #f5f7fa;
    font-family: system-ui, sans-serif;
}
main {
    max-width: 720px;
    padding: 48px;
    border-radius: 20px;
    background: white;
    box-shadow: 0 20px 60px rgba(0,0,0,.08);
    text-align: center;
}
</style>
</head>
<body>
<main>
    <h1>Generated Webpage</h1>
    <p>This page was created by the local AI workbench.</p>
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

    if ext == ".js":
        return """console.log("Generated JavaScript file");
"""

    if ext == ".css":
        return """body {
    margin: 0;
    font-family: system-ui, sans-serif;
}
"""

    if ext == ".json":
        return """{
  "generated": true,
  "source": "Sovereign Industrial AI Workbench"
}
"""

    return ""


def generate_prompt(
    request: str,
    extension: str,
    context: str = "",
) -> str:

    prompt = f"""
You are the artifact-generation worker of a local AI agent.

The application will save your output directly to disk.

TASK:
Generate the complete contents of a {extension} file.

STRICT RULES:
- Return ONLY the file contents.
- Do not converse.
- Do not say "Sure".
- Do not say "I can help".
- Do not say "Here is".
- Do not say "I cannot".
- Do not output "Assistant:".
- Do not output markdown fences.
- Do not output control tokens.
- Do not tell the user what they need to do.
- Actually generate the requested artifact.

USER REQUEST:
{request}
"""

    if extension == ".html":
        prompt += """

HTML RULES:
- Return a complete HTML document.
- Start with <!DOCTYPE html>.
- End with </html>.
- If the user asked for a UI, create the UI.
- If the user asked for Three.js, create a real Three.js scene.
- Do not leave placeholders such as "Your code here".
- Do not provide a tutorial instead of the page.
- Do not create a separate file unless requested.
"""

    if context:
        prompt += f"""

RECENT CONVERSATION CONTEXT:
{context[-6000:]}
"""

    return prompt


# Backward-compatible alias for the current GUI.
detect_file_request = detect_generation


# Backward-compatible API name used by main.py.
clean_file_content = clean_generated_content


# Backward-compatible API name used by main.py.
detect_file_request = detect_generation
