from __future__ import annotations

import re
from pathlib import Path


EDIT_WORDS = (
    "edit",
    "modify",
    "update",
    "change",
    "improve",
    "redesign",
    "revamp",
    "rewrite",
)


def detect_file_edit_request(text: str):
    q = " ".join(
        text.lower().split()
    )

    if not any(
        word in q
        for word in EDIT_WORDS
    ):
        return None

    file_markers = (
        "this file",
        "the file",
        "that file",
        ".html",
        ".htm",
        ".py",
        ".js",
        ".css",
        ".json",
    )

    if not any(
        marker in q
        for marker in file_markers
    ):
        return None

    filename = None

    patterns = (
        r"(?:file|named|called)\s+([A-Za-z0-9_.\-~/]+)",
        r"([A-Za-z0-9_.\-]+\.html)\b",
        r"([A-Za-z0-9_.\-]+\.py)\b",
        r"([A-Za-z0-9_.\-]+\.js)\b",
        r"([A-Za-z0-9_.\-]+\.css)\b",
    )

    for pattern in patterns:
        m = re.search(
            pattern,
            text,
            re.I,
        )
        if m:
            filename = m.group(1)
            break

    return {
        "filename": filename,
        "request": text,
    }


def resolve_edit_target(
    request: str,
    previous_file: str | None = None,
):
    req = detect_file_edit_request(
        request
    )

    if not req:
        return None

    if req["filename"]:
        candidate = Path(
            req["filename"]
        ).expanduser()

        if not candidate.is_absolute():
            candidate = (
                Path.home() / candidate
            )

        candidate = candidate.resolve()

        if candidate.exists():
            return candidate

    if (
        previous_file
        and Path(previous_file).exists()
    ):
        return Path(
            previous_file
        ).expanduser().resolve()

    return None


def clean_edited_content(
    text: str,
    extension: str,
):
    text = str(
        text or ""
    ).replace(
        "\r\n",
        "\n",
    ).strip()

    for token in (
        "<|im_end|>",
        "<|im_start|>",
        "<|endoftext|>",
        "<|eot_id|>",
    ):
        text = text.replace(
            token,
            "",
        )

    ext = extension.lower()

    if ext in (
        ".html",
        ".htm",
    ):

        marker = re.search(
            r"<!DOCTYPE\s+html\b",
            text,
            re.I,
        )

        if not marker:
            marker = re.search(
                r"<html\b",
                text,
                re.I,
            )

        if not marker:
            raise ValueError(
                "Model did not return a valid HTML document."
            )

        text = text[
            marker.start():
        ]

        end = re.search(
            r"</html\s*>",
            text,
            re.I,
        )

        if not end:
            raise ValueError(
                "Edited HTML is incomplete."
            )

        return text[
            :end.end()
        ].strip()

    # Generic code cleanup.
    text = re.sub(
        r"^\s*Assistant\s*:\s*",
        "",
        text,
        count=1,
        flags=re.I,
    )

    fence = re.match(
        r"^\s*```[A-Za-z0-9_+-]*\s*\n?"
        r"([\s\S]*?)"
        r"\n?```\s*$",
        text,
        re.I,
    )

    if fence:
        text = fence.group(1).strip()

    return text.strip()


def overwrite_verified_file(
    target: Path,
    content: str,
):
    target = target.expanduser().resolve()

    if not target.exists():
        raise FileNotFoundError(
            str(target)
        )

    if not target.is_file():
        raise ValueError(
            f"Not a regular file: {target}"
        )

    target.write_text(
        content,
        encoding="utf-8",
    )

    if not target.exists():
        raise RuntimeError(
            "Edited file no longer exists."
        )

    if target.stat().st_size == 0:
        raise RuntimeError(
            "Edited file is empty."
        )

    return target
