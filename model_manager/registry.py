"""Model Registry Configuration & Metadata Store for Sovereign Industrial Operations.

Manages definitions for the 500M Organizer and open-weight specialist workers.
DO NOT hardcode filenames in business logic: swapping models requires editing this
registry or updating configuration files, not touching workflow or policy engines.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from model_manager.adapters.base import BaseModelAdapter
from model_manager.adapters.mock_dev_adapter import MockDevAdapter
from model_manager.adapters.llama_cpp_adapter import LlamaCppAdapter


@dataclass
class WorkerModelDefinition:
    worker_type: str  # organizer, general, coding, vision, document
    model_name: str
    file_path: Optional[str] = None
    checksum_sha256: Optional[str] = None
    license: str = "Apache-2.0"
    capabilities: List[str] = field(default_factory=list)
    vram_required_mb: int = 2048
    ram_required_mb: int = 4096
    adapter_type: str = "mock"  # mock, llama_cpp, vllm
    endpoint: Optional[str] = None
    adapter: Optional[BaseModelAdapter] = None


class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, WorkerModelDefinition] = {}
        self._init_default_registry()

    def _init_default_registry(self) -> None:
        """Initializes default registry profiles for the 500M Organizer and local workers."""
        # 1. 500M Organizer Model (Controller)
        self.register_worker(
            WorkerModelDefinition(
                worker_type="organizer",
                model_name="Organizer-500M-Industrial-v1",
                file_path="models/organizer_500m.gguf",
                checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                license="Apache-2.0",
                capabilities=["intent_classification", "workflow_decomposition", "routing", "observation", "recovery"],
                vram_required_mb=1200,
                ram_required_mb=2048,
                adapter=MockDevAdapter("organizer", "Organizer-500M-Industrial-v1", 1200, 2048),
            )
        )

        # 2. General Reasoning Worker (e.g. Qwen2.5-3B-Instruct)
        self.register_worker(
            WorkerModelDefinition(
                worker_type="general",
                model_name="Qwen2.5-3B-Instruct-Q4_K_M",
                file_path="models/qwen2.5_3b_instruct.gguf",
                checksum_sha256="a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef",
                license="Apache-2.0",
                capabilities=["reasoning", "summarization", "synthesis", "audit_note_generation"],
                vram_required_mb=3200,
                ram_required_mb=4096,
                adapter=MockDevAdapter("general", "Qwen2.5-3B-Instruct-Q4_K_M", 3200, 4096),
            )
        )

        # 3. Coding Specialist Worker (e.g. StarCoder2-3B-Instruct)
        self.register_worker(
            WorkerModelDefinition(
                worker_type="coding",
                model_name="StarCoder2-3B-Instruct-Q4_K_M",
                file_path="models/starcoder2_3b_instruct.gguf",
                checksum_sha256="c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef1234",
                license="BigCode OpenRAIL-M v1",
                capabilities=["python", "engineering_math", "api510_calc", "data_processing", "debugging"],
                vram_required_mb=3000,
                ram_required_mb=4096,
                adapter=MockDevAdapter("coding", "StarCoder2-3B-Instruct-Q4_K_M", 3000, 4096),
            )
        )

        # 4. Vision / Multimodal Specialist Worker (e.g. Qwen2.5-VL-3B-Instruct)
        self.register_worker(
            WorkerModelDefinition(
                worker_type="vision",
                model_name="Qwen2.5-VL-3B-Instruct-Q4_K_M",
                file_path="models/qwen2.5_vl_3b.gguf",
                checksum_sha256="d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef123456",
                license="Apache-2.0",
                capabilities=["diagram_analysis", "pid_inspection", "scanned_doc_ocr", "defect_detection"],
                vram_required_mb=4100,
                ram_required_mb=6144,
                adapter=MockDevAdapter("vision", "Qwen2.5-VL-3B-Instruct-Q4_K_M", 4100, 6144),
            )
        )

        # 5. Document / Local RAG Specialist Worker (e.g. Gemma 3 4B / Qwen)
        self.register_worker(
            WorkerModelDefinition(
                worker_type="document",
                model_name="Gemma-3-4B-IT-Q4_K_M",
                file_path="models/gemma3_4b_it.gguf",
                checksum_sha256="e5f678901234567890abcdef1234567890abcdef1234567890abcdef12345678",
                license="Gemma Terms of Use",
                capabilities=["rag_synthesis", "sop_comparison", "table_extraction", "compliance_audit"],
                vram_required_mb=3600,
                ram_required_mb=4096,
                adapter=MockDevAdapter("document", "Gemma-3-4B-IT-Q4_K_M", 3600, 4096),
            )
        )

    def register_worker(self, definition: WorkerModelDefinition) -> None:
        self._models[definition.worker_type] = definition

    def get_worker(self, worker_type: str) -> Optional[WorkerModelDefinition]:
        return self._models.get(worker_type.lower())

    def list_workers(self) -> List[Dict[str, Any]]:
        return [
            {
                "worker_type": defn.worker_type,
                "model_name": defn.model_name,
                "capabilities": defn.capabilities,
                "vram_required_mb": defn.vram_required_mb,
                "ram_required_mb": defn.ram_required_mb,
                "license": defn.license,
                "is_loaded": defn.adapter.is_loaded() if defn.adapter else False,
            }
            for defn in self._models.values()
        ]


REGISTRY = ModelRegistry()
