"""Base Model Adapter Interface for Sovereign Industrial Operations.

Every worker model (Organizer, General, Coding, Vision, Document) implements this interface,
ensuring the application is completely decoupled from underlying inference runtimes (llama.cpp,
llama-server, vLLM, transformers, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generator, Optional


@dataclass
class WorkerInferenceResponse:
    worker_type: str
    status: str  # success, error, timeout
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    tokens_generated: int = 0
    latency_ms: float = 0.0
    vram_used_mb: int = 0
    error_message: Optional[str] = None


class BaseModelAdapter(ABC):
    @abstractmethod
    def load(self, model_path: Optional[str] = None, gpu_layers: int = -1) -> bool:
        """Loads model weights into VRAM/RAM."""
        pass

    @abstractmethod
    def unload(self) -> bool:
        """Frees VRAM/RAM and releases worker resources."""
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Returns True if the model is currently resident in memory."""
        pass

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> WorkerInferenceResponse:
        """Performs synchronous inference with latency and resource tracking."""
        pass

    @abstractmethod
    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        """Streams user-facing response chunks."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Returns worker health and resource metrics."""
        pass
