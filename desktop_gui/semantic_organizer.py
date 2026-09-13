from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class UserIntent:
    intent: str = "CHAT"
    confidence: float = 0.0
    execute: bool = False
    action: str | None = None
    target: str | None = None
    file_type: str | None = None
    path: str | None = None
    requirements: list[str] = field(default_factory=list)
    model: str | None = None
    needs_clarification: bool = False
    clarification: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


ALLOWED = {
    "CHAT",
    "CODING",
    "CREATE_FILE",
    "EDIT_FILE",
    "READ_FILE",
    "RUN_CODE",
    "RUN_COMMAND",
    "VISION",
    "DOCUMENT",
    "RAG",
    "WORKFLOW",
    "CLARIFY",
}


def normalize(text: str) -> str:
    text = str(text or "").lower()

    replacements = {
        "genrate": "generate",
        "generte": "generate",
        "gernerate": "generate",
        "gnrate": "generate",
        "direcotry": "directory",
        "direcotyr": "directory",
        "dowloads": "downloads",
        "downlods": "downloads",
        "pyhton": "python",
        "javasript": "javascript",
        "htmll": "html",
        "therr js": "three js",
        "threejs": "three js",
        "bnna": "bana",
        "bna": "bana",
        "bnao": "banao",
        "bnado": "bana do",
        "krdo": "kar do",
        "karo": "karo",
        "kro": "karo",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())


def extract_json(text: str) -> dict[str, Any] | None:
    text = str(text or "").strip()

    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    match = re.search(
        r"```json\s*([\s\S]*?)```",
        text,
        re.I,
    )

    if match:
        try:
            obj = json.loads(match.group(1))
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        try:
            obj = json.loads(
                text[start:end + 1]
            )
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    return None


def infer_type(q: str) -> str | None:
    if "three js" in q and (
        "html" in q
        or "web page" in q
        or "webpage" in q
        or "page" in q
        or "file" in q
    ):
        return ".html"

    if any(x in q for x in (
        "html",
        "webpage",
        "web page",
    )):
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

    return None


def infer_directory(
    q: str,
    fallback: str | None = None,
):
    if "downloads" in q or "download" in q:
        return Path.home() / "Downloads", True

    if "desktop" in q:
        return Path.home() / "Desktop", True

    if "documents" in q:
        return Path.home() / "Documents", True

    if "home directory" in q or "home folder" in q:
        return Path.home(), True

    if "in home" in q:
        return Path.home(), True

    if fallback:
        return (
            Path(fallback).expanduser().resolve(),
            False,
        )

    return None, False


def infer_filename(
    text: str,
    extension: str,
):
    for pattern in (
        r"(?:named|called)\s+([A-Za-z0-9_.-]+)",
        r"\b([A-Za-z0-9_.-]+\.(?:py|html?|css|js|ts|json|md|txt|csv|yaml|yml|xml|sql|sh))\b",
    ):
        match = re.search(
            pattern,
            text,
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
                "folder",
                "directory",
            }:
                return candidate

    if extension == ".html":
        return "generated_page.html"

    if extension == ".py":
        return "generated_script.py"

    if extension == ".js":
        return "generated_script.js"

    if extension == ".css":
        return "generated_style.css"

    return "generated_file" + extension


def fallback_intent(
    message: str,
    *,
    last_file: str | None = None,
    last_directory: str | None = None,
    pending_intent: str | None = None,
) -> UserIntent:

    q = normalize(message)

    # --------------------------------------------------------
    # CONTINUE PREVIOUS ACTION
    # --------------------------------------------------------

    if pending_intent:
        directory, explicit = infer_directory(
            q,
            fallback=last_directory,
        )

        if directory is not None:
            ext = infer_type(q)

            if pending_intent == "CREATE_FILE":
                ext = ext or ".html"
                filename = infer_filename(
                    message,
                    ext,
                )

                return UserIntent(
                    intent="CREATE_FILE",
                    action="create_file",
                    execute=True,
                    confidence=0.97,
                    file_type=ext,
                    path=str(
                        directory / filename
                    ),
                )

            if pending_intent == "EDIT_FILE":
                return UserIntent(
                    intent="EDIT_FILE",
                    action="edit_file",
                    execute=True,
                    confidence=0.97,
                    target=last_file,
                )

    # --------------------------------------------------------
    # EDIT / IMPROVE / REDESIGN
    # --------------------------------------------------------

    if any(
        x in q
        for x in (
            "edit this file",
            "edit the file",
            "modify this file",
            "update this file",
            "improve this file",
            "improve this page",
            "redesign this page",
            "redesign it",
            "make it beautiful",
            "make this page",
            "change this html",
            "make it better",
            "improve it",
        )
    ):

        if last_file:
            return UserIntent(
                intent="EDIT_FILE",
                action="edit_file",
                execute=True,
                confidence=0.96,
                target=last_file,
            )

        return UserIntent(
            intent="CLARIFY",
            confidence=0.94,
            needs_clarification=True,
            clarification=(
                "Which file should I edit?"
            ),
        )


    # --------------------------------------------------------
    # NATURAL FILE-CREATION LANGUAGE
    # --------------------------------------------------------
    #
    # Treat "<type> file" as a file artifact request even when
    # the user does not use the exact phrase "generate a file".
    #
    natural_file_phrases = (
        "make cpython file",
        "create cpython file",
        "generate cpython file",
        "write cpython file",
        "make python file",
        "create python file",
        "generate python file",
        "write python file",
        "python file bana",
        "python file banao",
        "make html file",
        "create html file",
        "generate html file",
        "write html file",
        "make css file",
        "create css file",
        "generate css file",
        "make javascript file",
        "create javascript file",
        "generate javascript file",
        "make js file",
        "create js file",
        "generate js file",
        "make json file",
        "create json file",
        "generate json file",
    )

    natural_type_words = (
        "cpython file",
        "python file",
        "html file",
        "css file",
        "javascript file",
        "js file",
        "json file",
    )

    natural_file_request = (
        any(
            phrase in q
            for phrase in natural_file_phrases
        )
        or (
            any(
                phrase in q
                for phrase in natural_type_words
            )
            and any(
                verb in q
                for verb in (
                    "make",
                    "create",
                    "generate",
                    "write",
                    "bana",
                    "banao",
                )
            )
        )
    )

    if natural_file_request:

        if (
            "html" in q
            or "webpage" in q
            or "web page" in q
        ):
            ext = ".html"

        elif (
            "javascript" in q
            or "js file" in q
        ):
            ext = ".js"

        elif "css" in q:
            ext = ".css"

        elif "json" in q:
            ext = ".json"

        else:
            ext = ".py"

        directory, _ = infer_directory(
            q,
            fallback=last_directory,
        )

        if directory is None:
            directory = Path.home()

        # Preserve explicit cpython name.
        if "cpython" in q:
            filename = "cpython.py"
        else:
            filename = infer_filename(
                message,
                ext,
            )

        return UserIntent(
            intent="CREATE_FILE",
            action="create_file",
            execute=True,
            confidence=0.99,
            file_type=ext,
            path=str(
                directory / filename
            ),
            requirements=[],
        )


    # --------------------------------------------------------
    # FILE CREATION — ENGLISH + HINGLISH
    # --------------------------------------------------------

    creation = any(
        x in q
        for x in (
            "generate a file",
            "generate file",
            "create a file",
            "make a file",
            "write a file",
            "save as a file",
            "file bana",
            "file banao",
            "file ban",
            "page bana",
            "page banao",
            "generate python file",
            "create python file",
            "generate html file",
            "create html file",
            "generate a three js",
        )
    )

    # Short requests such as:
    # "html file" / "python file"
    if (
        not creation
        and (
            q.strip() in {
                "html file",
                "python file",
                "py file",
                "css file",
                "json file",
                "javascript file",
                "js file",
            }
        )
    ):
        creation = True

    if creation:

        ext = infer_type(q) or ".txt"

        directory, explicit = infer_directory(
            q,
            fallback=last_directory,
        )

        if directory is None:
            directory = Path.home()

        filename = infer_filename(
            message,
            ext,
        )

        requirements = []

        if (
            "three js" in q
            or "3d" in q
        ):
            requirements.append(
                "Three.js"
            )

        if "beautiful" in q:
            requirements.append(
                "polished modern UI"
            )

        return UserIntent(
            intent="CREATE_FILE",
            action="create_file",
            execute=True,
            confidence=0.97,
            file_type=ext,
            path=str(
                directory / filename
            ),
            requirements=requirements,
        )

    # --------------------------------------------------------
    # EXPLICIT COMMAND
    # --------------------------------------------------------

    if any(
        x in q
        for x in (
            "run command",
            "execute command",
            "run this command",
            "run in terminal",
            "terminal command",
        )
    ):
        return UserIntent(
            intent="RUN_COMMAND",
            action="terminal",
            execute=True,
            confidence=0.94,
        )

    # --------------------------------------------------------
    # VISION / DOCUMENT
    # --------------------------------------------------------

    if any(
        x in q
        for x in (
            "analyze this image",
            "look at this image",
            "what is in this image",
            "p&id",
        )
    ):
        return UserIntent(
            intent="VISION",
            execute=True,
            confidence=0.93,
        )

    if any(
        x in q
        for x in (
            "read this pdf",
            "read this document",
            "summarize this file",
            "analyze this report",
        )
    ):
        return UserIntent(
            intent="DOCUMENT",
            execute=True,
            confidence=0.93,
        )

    # --------------------------------------------------------
    # CODING
    # --------------------------------------------------------

    if any(
        x in q
        for x in (
            "generate python code",
            "write python code",
            "python code",
            "write code",
            "debug this code",
            "javascript code",
            "sql query",
        )
    ):
        return UserIntent(
            intent="CODING",
            execute=True,
            confidence=0.92,
            model="coding",
        )

    # --------------------------------------------------------
    # ENGINEERING WORKFLOW
    # --------------------------------------------------------

    if any(
        x in q
        for x in (
            "remaining life",
            "corrosion rate",
            "inspection",
            "efficiency calculation",
            "thermodynamic",
            "approval note",
            "safety verification",
        )
    ):
        return UserIntent(
            intent="WORKFLOW",
            execute=True,
            confidence=0.92,
        )

    return UserIntent(
        intent="CHAT",
        execute=False,
        confidence=0.70,
    )


class SemanticOrganizer:

    def __init__(
        self,
        model_manager_getter,
    ):
        self._get_manager = model_manager_getter

    def organize(
        self,
        message: str,
        *,
        context: str = "",
        state=None,
        has_attachment: bool = False,
    ) -> UserIntent:

        last_file = (
            getattr(
                state,
                "last_file",
                None,
            )
            if state
            else None
        )

        last_directory = (
            getattr(
                state,
                "last_directory",
                None,
            )
            if state
            else None
        )

        pending_intent = (
            getattr(
                state,
                "pending_intent",
                None,
            )
            if state
            else None
        )

        fallback = fallback_intent(
            message,
            last_file=last_file,
            last_directory=last_directory,
            pending_intent=pending_intent,
        )

        mm = None

        try:
            mm = self._get_manager()
        except Exception:
            mm = None

        if mm is None:
            return fallback

        state_dump = (
            state.snapshot()
            if state and hasattr(state, "snapshot")
            else {}
        )

        prompt = f"""
You are the semantic conversation organizer for a local AI agent.

You do NOT answer the user.
You do NOT generate code.
You decide what the user MEANS and what the application should DO.

You must understand:
- normal English
- Hinglish
- typos
- short requests
- follow-up messages
- implied continuation
- "this file", "it", "that", "same one"
- current conversation
- previous generated files
- pending actions
- requested location

Important distinctions:

"generate python code"
=> CODING

"generate a python file"
=> CREATE_FILE

"make cpython file"
=> CREATE_FILE, file_type ".py"

"make cpython file in downloads"
=> CREATE_FILE, file_type ".py", Downloads

"make python code"
=> CODING

"generate python code"
=> CODING

"html file"
=> CREATE_FILE

"html file bnna"
=> CREATE_FILE

"genrate a therr js html file in hom"
=> CREATE_FILE, HTML, THREE.JS, HOME

"generate a three js page" 
=> CREATE_FILE, HTML, THREE.JS

"make it beautiful"
=> EDIT_FILE if a relevant previous file exists

"put it in downloads"
=> continue the pending/current file action

"hello"
=> CHAT

"explain this code"
=> CODING/CHAT depending on context, but do not modify files.

Return JSON only:

{{
  "intent": "CHAT|CODING|CREATE_FILE|EDIT_FILE|READ_FILE|RUN_CODE|RUN_COMMAND|VISION|DOCUMENT|RAG|WORKFLOW|CLARIFY",
  "confidence": 0.0,
  "execute": false,
  "action": null,
  "target": null,
  "file_type": null,
  "path": null,
  "requirements": [],
  "model": null,
  "needs_clarification": false,
  "clarification": null
}}

Rules:
- A user asking to CREATE/EDIT/RUN/READ something expects an actual action.
- Never claim that an action has happened. The executor will perform it.
- Do not confuse "code" with "file".
- Words such as "make", "create", "generate", "write", or
  Hinglish "bana/banao" combined with a file-type noun mean
  CREATE_FILE.
- "code" without a file/artifact request means CODING.
- "file" means an actual filesystem artifact is expected.
- Use context to resolve "it" and "this".
- Continue obvious pending tasks.
- Only ask for clarification if it materially changes what action should happen.
- For obvious requests, execute without asking.
- If the user says "here", "in home", "in downloads", resolve location.
- Return the most useful intent, not a vague description.

CONVERSATION STATE:
{json.dumps(state_dump, ensure_ascii=False)}

RECENT CONTEXT:
{context[-9000:]}

ATTACHMENT PRESENT:
{has_attachment}

CURRENT MESSAGE:
{message}

JSON ONLY.
""".strip()

        try:
            result = mm.run_worker(
                worker_type="organizer",
                prompt=prompt,
                request_id=None,
                max_tokens=700,
            )

            raw = getattr(
                result,
                "content",
                "",
            )

            data = extract_json(raw)

            if not data:
                return fallback

            intent_name = str(
                data.get(
                    "intent",
                    "CHAT",
                )
            ).upper().strip()

            if intent_name not in ALLOWED:
                return fallback

            confidence = float(
                data.get(
                    "confidence",
                    0.0,
                )
            )

            confidence = max(
                0.0,
                min(
                    1.0,
                    confidence,
                )
            )

            return UserIntent(
                intent=intent_name,
                confidence=confidence,
                execute=bool(
                    data.get(
                        "execute",
                        False,
                    )
                ),
                action=data.get("action"),
                target=data.get("target"),
                file_type=data.get("file_type"),
                path=data.get("path"),
                requirements=list(
                    data.get(
                        "requirements",
                        [],
                    )
                    or []
                ),
                model=data.get("model"),
                needs_clarification=bool(
                    data.get(
                        "needs_clarification",
                        False,
                    )
                ),
                clarification=data.get(
                    "clarification",
                ),
                raw=data,
            )

        except Exception:
            return fallback
