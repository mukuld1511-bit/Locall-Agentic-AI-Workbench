from __future__ import annotations

from pathlib import Path

from core.contracts import AttachmentContext, Intent


SHORT_ATTACHMENT_REQUESTS = {
    "what is this",
    "what is it",
    "what's this",
    "whats this",
    "explain this",
    "explain it",
    "read this",
    "read it",
    "look at this",
    "look over this",
    "check this",
    "check it",
    "analyze this",
    "analyse this",
    "describe this",
    "identify",
    "identify this",
    "what do you see",
    "tell me about this",
}


IMAGE_EXT = {
    ".png", ".jpg", ".jpeg", ".webp",
    ".bmp", ".gif"
}

DOCUMENT_EXT = {
    ".pdf", ".doc", ".docx",
    ".ppt", ".pptx", ".txt", ".md"
}

SHEET_EXT = {
    ".xlsx", ".xls", ".csv", ".tsv"
}

DB_EXT = {
    ".db", ".sqlite", ".sqlite3"
}


def attachment_context(path):

    if not path:
        return None

    p = Path(
        str(path)
    ).expanduser()

    # IMPORTANT:
    # Intent detection should work even when the test/UI gives
    # a future or not-yet-materialized path. The extension is
    # enough to understand the attachment type.
    suffix = p.suffix.lower()

    if suffix in IMAGE_EXT:
        kind = "image"

    elif suffix in DOCUMENT_EXT:
        kind = "document"

    elif suffix in SHEET_EXT:
        kind = "spreadsheet"

    elif suffix in DB_EXT:
        kind = "database"

    else:
        # A path without a recognized suffix is not enough to
        # infer an attachment modality.
        return None

    return AttachmentContext(
        path=str(
            p.resolve()
        ),
        name=p.name,
        suffix=suffix,
        kind=kind,
        is_image=suffix in IMAGE_EXT,
        is_document=suffix in DOCUMENT_EXT,
        is_spreadsheet=suffix in SHEET_EXT,
        is_database=suffix in DB_EXT,
    )



def resolve_intent(
    text: str,
    attachment=None,
) -> Intent:

    q = " ".join(
        str(text or "").lower().split()
    )

    att = attachment_context(
        attachment
    )

    # --------------------------------------------------------
    # ATTACHMENT FIRST
    # --------------------------------------------------------

    if att:

        refers_to_attachment = (
            q in SHORT_ATTACHMENT_REQUESTS
        )

        if att.is_image and (
            refers_to_attachment
            or any(
                x in q
                for x in (
                    "image",
                    "photo",
                    "picture",
                    "diagram",
                    "visual",
                    "identify",
                    "detect",
                    "recognize",
                    "recognise",
                    "inspect",
                    "look",
                    "see",
                    "show",
                    "describe",
                )
            )
        ):
            return Intent(
                action="ANALYZE_ATTACHMENT",
                worker="vision",
                confidence=0.99,
                attachment_required=True,
            )

        if att.is_spreadsheet and (
            refers_to_attachment
            or any(
                x in q
                for x in (
                    "excel",
                    "spreadsheet",
                    "sheet",
                    "table",
                    "calculate",
                    "analyze",
                    "analyse",
                    "read",
                )
            )
        ):
            return Intent(
                action="ANALYZE_ATTACHMENT",
                worker="document",
                confidence=0.95,
                attachment_required=True,
            )

        if att.is_database and (
            refers_to_attachment
            or any(
                x in q
                for x in (
                    "database",
                    "db",
                    "sql",
                    "query",
                    "schema",
                    "table",
                    "analyze",
                    "analyse",
                    "read",
                )
            )
        ):
            return Intent(
                action="ANALYZE_DATABASE",
                worker="document",
                confidence=0.95,
                attachment_required=True,
            )

        if att.is_document and (
            refers_to_attachment
            or any(
                x in q
                for x in (
                    "read",
                    "summarize",
                    "summary",
                    "extract",
                    "report",
                    "document",
                    "review",
                    "analyze",
                    "analyse",
                )
            )
        ):
            return Intent(
                action="ANALYZE_ATTACHMENT",
                worker="document",
                confidence=0.95,
                attachment_required=True,
            )

    # --------------------------------------------------------
    # FILE CREATION != CODE GENERATION
    # --------------------------------------------------------

    explicit_file_terms = (
        "file",
        "document",
        "save as",
        "save it",
        "create a file",
        "make a file",
        "generate a file",
        "banao",
        "bana do",
        "file bana",
        "file banao",
    )

    code_terms = (
        "code",
        "snippet",
        "function",
        "program",
        "script",
        "implementation",
        "write code",
    )

    file_requested = any(
        term in q
        for term in explicit_file_terms
    )

    code_requested = any(
        term in q
        for term in code_terms
    )

    language_requested = any(
        term in q
        for term in (
            "python",
            "javascript",
            "typescript",
            "html",
            "css",
            "json",
            "yaml",
            "shell",
            "bash",
            "sql",
            "java",
            "c++",
            "cpp",
            "rust",
            "go",
            "ruby",
            "php",
            "kotlin",
        )
    )

    # Explicit FILE beats code only when the user actually said
    # file/document/save/create-file.
    if file_requested and language_requested:

        return Intent(
            action="CREATE_FILE",
            worker="coding",
            confidence=0.99,
        )

    # "generate python code" is coding, not file creation.
    if code_requested or language_requested:

        return Intent(
            action="GENERATE_CODE",
            worker="coding",
            confidence=0.96,
        )

    # --------------------------------------------------------
    # CODING
    # --------------------------------------------------------

    if any(
        x in q
        for x in (
            "python",
            "code",
            "script",
            "program",
            "function",
            "debug",
            "javascript",
            "typescript",
            "html",
            "css",
            "sql",
            "c++",
            "rust",
            "java",
        )
    ):
        return Intent(
            action="GENERATE_CODE",
            worker="coding",
            confidence=0.95,
        )

    # --------------------------------------------------------
    # INDUSTRIAL
    # --------------------------------------------------------

    if any(
        x in q
        for x in (
            "inspection",
            "corrosion",
            "remaining life",
            "efficiency",
            "thermodynamic",
            "safety",
            "engineering",
            "equipment",
        )
    ):
        return Intent(
            action="WORKFLOW",
            worker="workflow",
            confidence=0.90,
        )

    return Intent(
        action="CHAT",
        worker="general",
        confidence=0.80,
    )
