from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConversationState:
    last_intent: str | None = None
    last_action: str | None = None
    last_file: str | None = None
    last_directory: str | None = None
    last_model: str | None = None
    pending_intent: str | None = None
    pending_target: str | None = None
    recent_files: list[str] = field(default_factory=list)
    recent_artifacts: list[str] = field(default_factory=list)

    def remember_file(self, path: str | Path | None):
        if not path:
            return

        value = str(
            Path(path).expanduser().resolve()
        )

        self.last_file = value
        self.last_directory = str(
            Path(value).parent
        )

        self.recent_files = [
            x for x in self.recent_files
            if x != value
        ]

        self.recent_files.insert(
            0,
            value,
        )

        self.recent_files = self.recent_files[:20]

    def remember_artifact(self, path: str | Path | None):
        if not path:
            return

        value = str(
            Path(path).expanduser().resolve()
        )

        self.recent_artifacts = [
            x for x in self.recent_artifacts
            if x != value
        ]

        self.recent_artifacts.insert(
            0,
            value,
        )

        self.recent_artifacts = self.recent_artifacts[:20]

        self.remember_file(value)

    def set_pending(
        self,
        intent: str | None,
        target: str | None = None,
    ):
        self.pending_intent = intent
        self.pending_target = target

    def clear_pending(self):
        self.pending_intent = None
        self.pending_target = None

    def snapshot(self) -> dict:
        return {
            "last_intent": self.last_intent,
            "last_action": self.last_action,
            "last_file": self.last_file,
            "last_directory": self.last_directory,
            "last_model": self.last_model,
            "pending_intent": self.pending_intent,
            "pending_target": self.pending_target,
            "recent_files": list(self.recent_files),
            "recent_artifacts": list(self.recent_artifacts),
        }
