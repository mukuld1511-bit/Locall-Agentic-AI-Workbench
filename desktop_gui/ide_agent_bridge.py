from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


# Current local Workbench coding server.
CODING_URL = os.environ.get(
    "SOVEREIGN_CODING_URL",
    "http://127.0.0.1:8092/v1/chat/completions",
)


def clean(text: str) -> str:

    text = str(text or "")

    for token in (
        "<|im_end|>",
        "<|im_start|>",
        "<|endoftext|>",
    ):
        text = text.replace(
            token,
            "",
        )

    return text.strip()


def request_model(
    prompt: str,
    max_tokens: int = 4000,
) -> str:

    body = {
        "model": "local-coding",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the coding agent inside a local IDE. "
                    "Understand the user's request and current file "
                    "context. Return the requested solution directly. "
                    "Do not use Assistant: prefixes. "
                    "Do not emit model control tokens."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }

    data = json.dumps(
        body
    ).encode("utf-8")

    request = urllib.request.Request(
        CODING_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=180,
        ) as response:

            payload = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Local coding server unavailable: {exc}"
        )

    choices = payload.get(
        "choices",
        [],
    )

    if not choices:
        raise RuntimeError(
            "Coding model returned no choices."
        )

    message = choices[0].get(
        "message",
        {},
    )

    return clean(
        message.get(
            "content",
            "",
        )
    )


def extract_file_content(
    text: str,
    suffix: str,
) -> str:

    text = clean(text)

    if suffix.lower() in (
        ".html",
        ".htm",
    ):

        match = re.search(
            r"<!DOCTYPE\s+html\b",
            text,
            re.I,
        )

        if not match:

            match = re.search(
                r"<html\b",
                text,
                re.I,
            )

        if not match:
            raise ValueError(
                "Model did not return HTML."
            )

        text = text[
            match.start():
        ]

        end = re.search(
            r"</html\s*>",
            text,
            re.I,
        )

        if not end:
            raise ValueError(
                "Generated HTML is incomplete."
            )

        return text[
            :end.end()
        ].strip()

    # Markdown code fence.
    fence = re.match(
        r"^\s*```[^\n]*\n"
        r"([\s\S]*?)"
        r"\n```\s*$",
        text,
        re.I,
    )

    if fence:
        text = fence.group(1)

    # Strip conversational prefix.
    text = re.sub(
        r"^\s*Assistant\s*:\s*",
        "",
        text,
        count=1,
        flags=re.I,
    )

    return text.strip()


def edit_file(
    path: str,
    request: str,
):
    target = Path(
        path
    ).expanduser().resolve()

    existing = target.read_text(
        encoding="utf-8",
        errors="replace",
    )

    prompt = f"""
EDIT THE EXISTING FILE.

You must modify the existing file according to the user's request.

Return ONLY the complete replacement file.
Do not explain.
Do not say "Sure".
Do not say "I can help".
Do not say "Here is the code".
Do not output "Assistant:".
Do not use Markdown fences.
Do not output control tokens.

USER REQUEST:
{request}

FILE:
{target}

EXISTING CONTENT:
----------------
{existing}
----------------

Return the complete updated file.
"""

    raw = request_model(
        prompt,
        max_tokens=6000,
    )

    content = extract_file_content(
        raw,
        target.suffix,
    )

    if not content:
        raise RuntimeError(
            "AI returned empty edited content."
        )

    return content


def main():

    payload = json.loads(
        sys.stdin.read()
    )

    operation = payload.get(
        "operation"
    )

    if operation == "generate":

        suffix = payload.get(
            "suffix",
            ".txt",
        )

        prompt = payload["prompt"]

        system = f"""
FILE GENERATION MODE.

Generate a complete usable file of type {suffix}.

Return ONLY raw file contents.
No explanation.
No Assistant prefix.
No Markdown fences.
No control tokens.

If HTML is requested:
- return a complete document
- include <!DOCTYPE html>
- end with </html>
- implement requested UI/animation
- do not use placeholder content
"""

        raw = request_model(
            system
            + "\n\nUSER REQUEST:\n"
            + prompt,
            max_tokens=6000,
        )

        result = extract_file_content(
            raw,
            suffix,
        )

        print(
            json.dumps({
                "success": True,
                "content": result,
            })
        )

        return

    if operation == "edit":

        content = edit_file(
            payload["path"],
            payload["request"],
        )

        print(
            json.dumps({
                "success": True,
                "content": content,
            })
        )

        return

    raise ValueError(
        f"Unknown operation: {operation}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            json.dumps({
                "success": False,
                "error": str(exc),
            })
        )
        raise
