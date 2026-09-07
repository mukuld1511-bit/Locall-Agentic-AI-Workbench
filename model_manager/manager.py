"""Model Manager Service for Sovereign Industrial AI Workbench.

Key Capabilities:
- Strict VRAM Budget Enforcement on RTX 5060 (8192 MB total, 1024 MB OS reserve, 7168 MB active limit).
- Model Swapping & Eviction: Evicts idle specialist workers when VRAM budget would be exceeded.
- Worker Reuse: Consecutive steps utilizing the same model reuse the resident instance (0ms load overhead).
- Concurrency Control: Mutex locks prevent simultaneous conflicting loads/unloads.
- Latency & Resource Accounting: Measures load_ms, inference_ms, unload_ms for performance monitoring.
- Audit Trail: Emits structured audit records for all model lifecycle transitions.
"""

import threading
import time
from typing import Any, Dict, List, Optional
from backend.app.core.config import GLOBAL_CONFIG
from backend.app.audit.audit_service import AUDIT
from model_manager.registry import REGISTRY, WorkerModelDefinition
from model_manager.adapters.base import WorkerInferenceResponse


class ModelManager:
    def __init__(self):
        self.registry = REGISTRY
        self.vram_budget_mb = GLOBAL_CONFIG.VRAM_BUDGET_MB - GLOBAL_CONFIG.VRAM_RESERVE_MB  # e.g. 7168 MB
        self.lock = threading.RLock()
        self.active_workers: Dict[str, WorkerModelDefinition] = {}
        self.model_states: Dict[str, str] = {
            w["worker_type"]: "UNLOADED" for w in self.registry.list_workers()
        }
        self.metrics = {
            "swaps_count": 0,
            "reuses_count": 0,
            "total_load_time_ms": 0.0,
            "total_inference_time_ms": 0.0,
        }
        # Pre-warm organizer by default (essential lightweight controller)
        self.load_worker("organizer")

    def _set_model_state(self, worker_type: str, state: str) -> None:
        """Sets model state in state machine (UNLOADED -> LOADING -> READY -> RUNNING -> IDLE -> UNLOADING -> UNLOADED)."""
        worker = self.registry.get_worker(worker_type)
        key = worker.worker_type if worker else worker_type.lower()
        self.model_states[key] = state

    def get_model_state(self, worker_type: str) -> str:
        """Returns the current state machine state of a model."""
        with self.lock:
            worker = self.registry.get_worker(worker_type)
            key = worker.worker_type if worker else worker_type.lower()
            return self.model_states.get(key, "UNLOADED")

    def get_current_vram_used(self) -> int:
        with self.lock:
            return sum(w.vram_required_mb for w in self.active_workers.values())

    def is_loaded(self, worker_type: str) -> bool:
        with self.lock:
            worker = self.registry.get_worker(worker_type)
            if not worker or not worker.adapter:
                return False
            return worker.adapter.is_loaded()

    def load_worker(self, worker_type: str) -> bool:
        """Loads worker into memory, swapping out idle workers if VRAM budget exceeded."""
        with self.lock:
            worker = self.registry.get_worker(worker_type)
            if not worker or not worker.adapter:
                return False

            canonical_type = worker.worker_type

            if worker.adapter.is_loaded():
                self.active_workers[canonical_type] = worker
                self.metrics["reuses_count"] += 1
                self._set_model_state(canonical_type, "READY")
                return True

            # State transition: LOADING
            self._set_model_state(canonical_type, "LOADING")

            # Check if loading exceeds budget
            current_vram = self.get_current_vram_used()
            required_vram = worker.vram_required_mb

            if (current_vram + required_vram) > self.vram_budget_mb:
                # Need to evict idle worker(s), prioritizing non-organizer models
                evicted = self._evict_workers_for_budget(required_vram)
                if not evicted and (self.get_current_vram_used() + required_vram) > self.vram_budget_mb:
                    # Could not free enough memory
                    self._set_model_state(canonical_type, "UNLOADED")
                    return False

            # Perform load
            start_load = time.time()
            success = worker.adapter.load(worker.file_path)
            load_latency = (time.time() - start_load) * 1000.0

            if success:
                self.active_workers[canonical_type] = worker
                self.metrics["total_load_time_ms"] += load_latency
                self._set_model_state(canonical_type, "READY")
                AUDIT.log_event(
                    event_type="MODEL_LOADED",
                    action="load_worker",
                    status="SUCCESS",
                    resource=f"model:{worker.model_name}",
                    details={
                        "worker_type": canonical_type,
                        "vram_mb": worker.vram_required_mb,
                        "load_latency_ms": round(load_latency, 2),
                        "total_vram_used_mb": self.get_current_vram_used(),
                        "state": "READY",
                    },
                )
                return True
            else:
                self._set_model_state(canonical_type, "UNLOADED")
                return False

    def unload_worker(self, worker_type: str) -> bool:
        """Unloads worker from memory."""
        with self.lock:
            worker = self.registry.get_worker(worker_type)
            if not worker or not worker.adapter or not worker.adapter.is_loaded():
                if worker:
                    self._set_model_state(worker.worker_type, "UNLOADED")
                return True

            canonical_type = worker.worker_type

            # State transition: UNLOADING
            self._set_model_state(canonical_type, "UNLOADING")

            start_unload = time.time()
            worker.adapter.unload()
            unload_latency = (time.time() - start_unload) * 1000.0

            if canonical_type in self.active_workers:
                del self.active_workers[canonical_type]

            # State transition: UNLOADED
            self._set_model_state(canonical_type, "UNLOADED")

            AUDIT.log_event(
                event_type="MODEL_UNLOADED",
                action="unload_worker",
                status="SUCCESS",
                resource=f"model:{worker.model_name}",
                details={
                    "worker_type": canonical_type,
                    "freed_vram_mb": worker.vram_required_mb,
                    "unload_latency_ms": round(unload_latency, 2),
                    "remaining_vram_mb": self.get_current_vram_used(),
                    "state": "UNLOADED",
                },
            )
            return True

    def _evict_workers_for_budget(self, required_vram: int) -> bool:
        """Evicts resident non-organizer workers until required VRAM is available."""
        # Candidates for eviction: any active worker that is NOT the organizer
        eviction_candidates = [
            wt for wt in self.active_workers.keys() if wt != "organizer"
        ]
        
        for candidate in eviction_candidates:
            self.unload_worker(candidate)
            self.metrics["swaps_count"] += 1
            if (self.get_current_vram_used() + required_vram) <= self.vram_budget_mb:
                return True
        return (self.get_current_vram_used() + required_vram) <= self.vram_budget_mb

    def run_worker(
        self,
        worker_type: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> WorkerInferenceResponse:
        """Routes task to worker, ensuring model is loaded, tracking latency and audit trail."""
        worker_type = worker_type.lower()
        with self.lock:
            # Step 1: Ensure worker is loaded
            if not self.is_loaded(worker_type):
                loaded = self.load_worker(worker_type)
                if not loaded:
                    return WorkerInferenceResponse(
                        worker_type=worker_type,
                        status="error",
                        content="",
                        error_message=f"Model Manager failed to load worker '{worker_type}' due to memory constraints.",
                    )

            worker = self.registry.get_worker(worker_type)
            if not worker or not worker.adapter:
                return WorkerInferenceResponse(
                    worker_type=worker_type,
                    status="error",
                    content="",
                    error_message=f"Worker '{worker_type}' not found in registry.",
                )

            # Step 2: Inference execution
            AUDIT.log_event(
                event_type="MODEL_SELECTED",
                action="run_worker",
                status="RUNNING",
                resource=f"model:{worker.model_name}",
                request_id=request_id,
                details={"worker_type": worker_type},
            )

            canonical_type = worker.worker_type
            self._set_model_state(canonical_type, "RUNNING")

            start_infer = time.time()
            try:
                resp = worker.adapter.generate(prompt, system_prompt, **kwargs)
            finally:
                self._set_model_state(canonical_type, "IDLE")
            infer_latency = (time.time() - start_infer) * 1000.0

            self.metrics["total_inference_time_ms"] += infer_latency

            AUDIT.log_event(
                event_type="MODEL_INFERENCE_COMPLETE",
                action="run_worker",
                status="SUCCESS" if resp.status == "success" else "FAILED",
                resource=f"model:{worker.model_name}",
                request_id=request_id,
                details={
                    "worker_type": worker_type,
                    "latency_ms": round(infer_latency, 2),
                    "tokens": resp.tokens_generated,
                },
            )

            return resp

    def get_system_status(self) -> Dict[str, Any]:
        """Returns comprehensive hardware and model state for UI & health checks."""
        with self.lock:
            current_vram = self.get_current_vram_used()
            return {
                "target_device": GLOBAL_CONFIG.TARGET_DEVICE,
                "vram_budget_mb": self.vram_budget_mb + GLOBAL_CONFIG.VRAM_RESERVE_MB,
                "vram_active_limit_mb": self.vram_budget_mb,
                "vram_current_used_mb": current_vram,
                "vram_headroom_mb": max(0, self.vram_budget_mb - current_vram),
                "active_workers": list(self.active_workers.keys()),
                "metrics": self.metrics,
                "workers": self.registry.list_workers(),
            }


MODEL_MGR = ModelManager()
