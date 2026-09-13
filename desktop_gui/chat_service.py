from __future__ import annotations

import re
import sqlite3
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "chat_history.db"



def generate_chat_title(text: str) -> str:
    """
    Generate a compact human-readable title from the user's
    first meaningful message. No model call is required.
    """

    text = " ".join(
        str(text or "").strip().split()
    )

    if not text:
        return "New Chat"

    q = text.lower()

    trivial = {
        "hi",
        "hii",
        "hello",
        "hey",
        "helo",
        "hiii",
        "good morning",
        "good evening",
        "thanks",
        "thank you",
    }

    if q in trivial:
        return "New Chat"

    # Strong domain phrases.
    mappings = (
        (
            (
                "three js",
                "three.js",
                "threejs",
            ),
            "Three.js",
        ),
        (
            (
                "python",
                "py file",
            ),
            "Python",
        ),
        (
            (
                "linear regression",
            ),
            "Linear Regression",
        ),
        (
            (
                "corrosion",
                "remaining life",
            ),
            "Remaining Life / Corrosion",
        ),
        (
            (
                "inspection report",
                "inspection",
            ),
            "Inspection Analysis",
        ),
        (
            (
                "sensor",
                "thermodynamic",
                "efficiency",
            ),
            "Sensor & Efficiency Analysis",
        ),
        (
            (
                "html",
                "webpage",
                "web page",
            ),
            "HTML Webpage",
        ),
        (
            (
                "database",
                "sqlite",
                "sql",
                "db ",
            ),
            "Database",
        ),
        (
            (
                "p&id",
                "pid",
            ),
            "P&ID Analysis",
        ),
    )

    for keywords, title in mappings:
        if any(
            keyword in q
            for keyword in keywords
        ):
            # Add useful filename / equipment token when present.
            match = re.search(
                r"\b([A-Z]{1,6}-\d{2,6})\b",
                text,
            )

            if match:
                return f"{match.group(1)} {title}"

            return title

    # Action-oriented titles.
    if any(
        x in q
        for x in (
            "generate",
            "create",
            "make",
            "build",
            "write",
        )
    ):
        cleaned = re.sub(
            r"\b(generate|create|make|build|write)\b",
            "",
            text,
            flags=re.I,
        ).strip()

        if cleaned:
            text = cleaned

    # Keep titles compact.
    words = text.split()

    if len(words) > 6:
        words = words[:6]

    title = " ".join(words).strip()

    if not title:
        return "New Chat"

    title = title[0].upper() + title[1:]

    return title[:52]



class ChatService:


    def get_chat_title(
        self,
        chat_id,
        user_id,
    ):
        with sqlite3.connect(DB_PATH) as db:
            row = db.execute(
                """
                SELECT title
                FROM chats
                WHERE chat_id = ?
                  AND user_id = ?
                LIMIT 1
                """,
                (
                    chat_id,
                    user_id,
                ),
            ).fetchone()

            return row[0] if row else None




    def rename_chat(
        self,
        chat_id,
        user_id,
        title,
    ):
        title = " ".join(
            str(title or "").split()
        ).strip()

        if not title:
            title = "New Chat"

        with sqlite3.connect(DB_PATH) as db:
            db.execute(
                """
                UPDATE chats
                SET title = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ?
                  AND user_id = ?
                """,
                (
                    title[:80],
                    chat_id,
                    user_id,
                ),
            )
            db.commit()



    def __init__(self):
        DB_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._init()

    def _init(self):
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            db.commit()

    def new_chat(
        self,
        user_id: str,
        title: str = "New Chat",
    ):
        chat_id = uuid.uuid4().hex

        with sqlite3.connect(DB_PATH) as db:
            db.execute(
                """
                INSERT INTO chats
                (chat_id,user_id,title)
                VALUES (?,?,?)
                """,
                (
                    chat_id,
                    user_id,
                    title[:120],
                ),
            )
            db.commit()

        return chat_id

    def save_message(
        self,
        chat_id,
        user_id,
        role,
        content,
        model="",
    ):
        with sqlite3.connect(DB_PATH) as db:
            db.execute(
                """
                INSERT INTO messages
                (chat_id,user_id,role,content,model)
                VALUES (?,?,?,?,?)
                """,
                (
                    chat_id,
                    user_id,
                    role,
                    str(content),
                    model,
                ),
            )

            db.execute(
                """
                UPDATE chats
                SET updated_at=CURRENT_TIMESTAMP
                WHERE chat_id=? AND user_id=?
                """,
                (
                    chat_id,
                    user_id,
                ),
            )

            db.commit()

    def list_chats(
        self,
        user_id,
        limit=50,
    ):
        with sqlite3.connect(DB_PATH) as db:
            return db.execute(
                """
                SELECT chat_id,title,created_at,updated_at
                FROM chats
                WHERE user_id=?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (
                    user_id,
                    limit,
                ),
            ).fetchall()

    def messages(
        self,
        chat_id,
        user_id,
        limit=30,
    ):
        with sqlite3.connect(DB_PATH) as db:
            return db.execute(
                """
                SELECT role,content,model,created_at
                FROM messages
                WHERE chat_id=? AND user_id=?
                ORDER BY id ASC
                LIMIT ?
                """,
                (
                    chat_id,
                    user_id,
                    limit,
                ),
            ).fetchall()

    def context(
        self,
        chat_id,
        user_id,
        limit=12,
    ):
        """
        Return recent conversation as clean, non-recursive context.

        IMPORTANT:
        The caller may have already saved the current user message.
        Therefore the latest user message is excluded here. The
        current request is added exactly once by build_prompt().
        """

        rows = self.messages(
            chat_id,
            user_id,
            limit + 1,
        )

        if not rows:
            return ""

        # If the newest stored message is a user message, it is
        # almost certainly the current request that send() just saved.
        # Do not inject it into history and then inject it again.
        if rows[-1][0].lower() == "user":
            rows = rows[:-1]

        rows = rows[-limit:]

        parts = []

        for role, content, model, created_at in rows:

            role = str(
                role or ""
            ).strip().lower()

            content = str(
                content or ""
            ).strip()

            if not content:
                continue

            # Remove control/template artifacts from old messages.
            for token in (
                "<|im_start|>",
                "<|im_end|>",
                "<|endoftext|>",
                "<|eot_id|>",
            ):
                content = content.replace(
                    token,
                    "",
                )

            if role == "user":
                parts.append(
                    "[PREVIOUS USER]\n"
                    + content
                )

            elif role == "assistant":
                parts.append(
                    "[PREVIOUS ASSISTANT]\n"
                    + content
                )

        return "\n\n".join(parts)

