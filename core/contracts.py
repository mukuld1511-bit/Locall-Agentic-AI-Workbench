from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class WorkerResponse:
    worker_type: str
    status: str
    content: str = ""
    tokens_generated: int = 0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttachmentContext:
    path: str
    name: str
    suffix: str
    kind: str
    is_image: bool = False
    is_document: bool = False
    is_spreadsheet: bool = False
    is_database: bool = False


@dataclass
class Intent:
    action: str
    worker: str
    confidence: float = 1.0
    attachment_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
