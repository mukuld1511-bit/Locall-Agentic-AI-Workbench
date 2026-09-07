"""Mock / Development Adapter for Local Testing & Hardware Profiling.

Provides high-fidelity behavioral simulation of the 500M Organizer and open-weight specialist
workers (Qwen2.5-3B, StarCoder2-3B, Qwen2.5-VL-3B, Gemma-3-4B) before tomorrow's real weight
drop-in. Measures realistic latency, VRAM footprint, and structured outputs.
"""

import time
import json
from typing import Any, Dict, Generator, Optional
from model_manager.adapters.base import BaseModelAdapter, WorkerInferenceResponse


class MockDevAdapter(BaseModelAdapter):
    def __init__(self, worker_type: str, model_name: str, vram_mb: int, ram_mb: int):
        self.worker_type = worker_type
        self.model_name = model_name
        self.vram_mb = vram_mb
        self.ram_mb = ram_mb
        self._is_loaded = False
        self._load_timestamp = None
        self._total_inferences = 0

    def load(self, model_path: Optional[str] = None, gpu_layers: int = -1) -> bool:
        time.sleep(0.3)  # simulate loading latency
        self._is_loaded = True
        self._load_timestamp = time.time()
        return True

    def unload(self) -> bool:
        time.sleep(0.15)  # simulate clean VRAM deallocation
        self._is_loaded = False
        self._load_timestamp = None
        return True

    def is_loaded(self) -> bool:
        return self._is_loaded

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> WorkerInferenceResponse:
        if not self._is_loaded:
            return WorkerInferenceResponse(
                worker_type=self.worker_type,
                status="error",
                content="",
                error_message=f"Worker {self.worker_type} is not loaded in VRAM",
            )

        start_time = time.time()
        self._total_inferences += 1
        time.sleep(0.2)  # simulate inference latency on RTX 5060

        # Behavioral response based on worker capability
        if self.worker_type == "organizer":
            # Return structured planning action JSON
            if "inspection" in prompt.lower() or "scanned" in prompt.lower():
                plan = {
                    "task_type": "industrial_inspection_audit",
                    "steps": [
                        {"step": 1, "action": "Extract scanned report findings", "worker": "vision", "tool": "ocr"},
                        {"step": 2, "action": "Retrieve Refinery SOP for Heat Exchangers", "worker": "document", "tool": "rag_search"},
                        {"step": 3, "action": "Cross-reference findings against API 510 thresholds", "worker": "general"},
                        {"step": 4, "action": "Calculate corrosion rate & remaining life", "worker": "coding", "tool": "sandbox_exec"},
                        {"step": 5, "action": "Generate formal refinery Approval Note (.docx)", "worker": "document", "tool": "doc_generate"},
                    ]
                }
                content = json.dumps(plan, indent=2)
                structured = plan
            elif "efficiency" in prompt.lower() or "spreadsheet" in prompt.lower() or "calculate" in prompt.lower():
                plan = {
                    "task_type": "spreadsheet_efficiency_analysis",
                    "steps": [
                        {"step": 1, "action": "Read plant sensor log spreadsheet", "worker": "document", "tool": "spreadsheet_read"},
                        {"step": 2, "action": "Compute equipment thermodynamic efficiency", "worker": "coding", "tool": "sandbox_exec"},
                        {"step": 3, "action": "Generate executive efficiency report (.xlsx)", "worker": "document", "tool": "doc_generate"},
                    ]
                }
                content = json.dumps(plan, indent=2)
                structured = plan
            elif "p&id" in prompt.lower() or "piping" in prompt.lower():
                plan = {
                    "task_type": "pid_diagram_verification",
                    "steps": [
                        {"step": 1, "action": "Inspect P&ID tag topology and valves", "worker": "vision", "tool": "vision_analyze"},
                        {"step": 2, "action": "Check interlock logic against safety manual", "worker": "document", "tool": "rag_search"},
                        {"step": 3, "action": "Synthesize compliance verification report", "worker": "general"},
                    ]
                }
                content = json.dumps(plan, indent=2)
                structured = plan
            else:
                plan = {
                    "task_type": "standard_industrial_inquiry",
                    "steps": [
                        {"step": 1, "action": "Search refinery knowledge base", "worker": "document", "tool": "rag_search"},
                        {"step": 2, "action": "Synthesize verified engineering response", "worker": "general"},
                    ]
                }
                content = json.dumps(plan, indent=2)
                structured = plan

        elif self.worker_type == "vision":
            content = "Vision analysis extracted: Heat Exchanger E-1102 inspection report indicates Shell Wall Thickness = 8.4mm (Nominal: 12.0mm, Minimum Required: 6.5mm). Observed localized pitting at pass 2 baffle plate."
            structured = {"equipment_tag": "E-1102", "shell_thickness_mm": 8.4, "nominal_mm": 12.0, "min_required_mm": 6.5, "anomaly": "localized pitting"}

        elif self.worker_type == "coding":
            content = """# Equipment Remaining Life Calculation (API 510 Standard)
initial_thickness = 12.0  # mm
current_thickness = 8.4   # mm
operating_years = 6.0     # years
corrosion_rate = (initial_thickness - current_thickness) / operating_years  # mm/year
min_required = 6.5        # mm
remaining_life_years = (current_thickness - min_required) / corrosion_rate

result = {
    'corrosion_rate_mm_per_year': round(corrosion_rate, 3),
    'remaining_life_years': round(remaining_life_years, 2),
    'status': 'OPERATIONAL_WITH_MONITORING'
}
print(result)
"""
            structured = {"corrosion_rate_mm_per_year": 0.6, "remaining_life_years": 3.17, "status": "OPERATIONAL_WITH_MONITORING"}

        elif self.worker_type == "document":
            content = "Retrieved MRPL SOP-HEX-042: Section 4.3 mandates ultrasonic re-inspection every 24 months when remaining wall life is between 2.0 and 5.0 years."
            structured = {"sop_id": "MRPL-SOP-HEX-042", "clause": "4.3", "inspection_interval_months": 24}

        else:  # general worker
            content = (
                "Engineering Synthesis: Heat Exchanger E-1102 meets current API 510 minimum structural criteria (8.4mm > 6.5mm threshold). "
                "Calculated remaining operational life is 3.17 years at current corrosion rate (0.6 mm/yr). "
                "Per MRPL SOP-HEX-042 Clause 4.3, mandatory ultrasonic inspection must be scheduled within 24 months."
            )
            structured = {"compliant": True, "schedule_inspection_months": 24}

        latency = (time.time() - start_time) * 1000.0

        return WorkerInferenceResponse(
            worker_type=self.worker_type,
            status="success",
            content=content,
            structured_data=structured,
            tokens_generated=len(content.split()),
            latency_ms=round(latency, 2),
            vram_used_mb=self.vram_mb,
        )

    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        response = self.generate(prompt, system_prompt, **kwargs)
        for word in response.content.split():
            time.sleep(0.02)
            yield word + " "

    def health(self) -> Dict[str, Any]:
        return {
            "worker_type": self.worker_type,
            "model_name": self.model_name,
            "is_loaded": self._is_loaded,
            "vram_mb": self.vram_mb if self._is_loaded else 0,
            "total_inferences": self._total_inferences,
            "status": "READY" if self._is_loaded else "UNLOADED",
        }
