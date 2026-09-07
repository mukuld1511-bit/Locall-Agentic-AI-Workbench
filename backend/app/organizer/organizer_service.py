"""Organizer Controller Service for Sovereign Industrial Operations.

Manages the 500M Organizer Model interface:
1. Receives and classifies industrial tasks (Inspection, Coding, P&ID, Spreadsheet, RAG).
2. Decomposes tasks into structured, machine-readable action steps.
3. Specifies target specialist worker, required tool, and step dependencies.
4. Observes intermediate tool outputs and worker findings.
5. Diagnoses failures, handles retries, and verifies complete workflow satisfaction.
6. Returns validated user-facing communications without leaking internal prompt mechanisms.
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from backend.app.core.config import GLOBAL_CONFIG
from backend.app.audit.audit_service import AUDIT
from backend.app.security.sanitizer import SANITIZER
from model_manager.manager import MODEL_MGR


@dataclass
class WorkflowStepPlan:
    step_number: int
    action_name: str
    worker_type: str  # vision, coding, document, general
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)
    risk_level: str = "LOW"


@dataclass
class OrganizerDecomposition:
    task_type: str
    intent_summary: str
    steps: List[WorkflowStepPlan]
    raw_plan_json: str


class OrganizerService:
    def __init__(self):
        self.model_mgr = MODEL_MGR

    def plan_task(
        self,
        user_prompt: str,
        user_role: str,
        evidence_blocks: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> OrganizerDecomposition:
        """Invokes the 500M Organizer to understand intent and decompose task into structured steps."""
        system_instruction = (
            "You are the Sovereign Industrial Organizer (500M Controller). "
            "Your objective: Analyze the user's operational request, classify the task, and return a "
            "strict JSON plan containing task_type, intent_summary, and sequential execution steps. "
            "Each step must designate worker (vision, coding, document, general), optional tool, and dependencies."
        )

        # Apply security boundary wrapper
        context = SANITIZER.format_organizer_context(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            evidence_blocks=evidence_blocks or [],
        )

        AUDIT.log_event(
            event_type="ORGANIZER_PLANNING_STARTED",
            action="plan_task",
            status="RUNNING",
            role=user_role,
            request_id=request_id,
            details={"prompt_preview": user_prompt[:80]},
        )

        # Generate structured plan via Organizer
        organizer_resp = self.model_mgr.run_worker(
            worker_type="organizer",
            prompt=context,
            request_id=request_id,
            temperature=0.0,
        )

        # Parse plan
        raw_content = organizer_resp.content.strip()
        parsed_json = organizer_resp.structured_data
        
        if not parsed_json:
            try:
                # Attempt to extract JSON from raw content if string
                start_idx = raw_content.find("{")
                end_idx = raw_content.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    parsed_json = json.loads(raw_content[start_idx : end_idx + 1])
                else:
                    parsed_json = self._fallback_heuristic_plan(user_prompt)
            except Exception:
                parsed_json = self._fallback_heuristic_plan(user_prompt)

        steps: List[WorkflowStepPlan] = []
        raw_steps = parsed_json.get("steps", [])
        for idx, s in enumerate(raw_steps, start=1):
            steps.append(
                WorkflowStepPlan(
                    step_number=s.get("step", idx),
                    action_name=s.get("action", f"Step {idx}"),
                    worker_type=s.get("worker", "general"),
                    tool_name=s.get("tool"),
                    arguments=s.get("arguments", {}),
                    depends_on=s.get("depends_on", [idx - 1] if idx > 1 else []),
                    risk_level=s.get("risk_level", "LOW"),
                )
            )

        decomposition = OrganizerDecomposition(
            task_type=parsed_json.get("task_type", "general_workflow"),
            intent_summary=parsed_json.get("intent_summary", f"Execute plan for: {user_prompt[:60]}"),
            steps=steps,
            raw_plan_json=json.dumps(parsed_json, indent=2),
        )

        AUDIT.log_event(
            event_type="ORGANIZER_PLAN_PRODUCED",
            action="plan_task",
            status="SUCCESS",
            role=user_role,
            request_id=request_id,
            details={"task_type": decomposition.task_type, "steps_count": len(steps)},
        )

        return decomposition

    def _fallback_heuristic_plan(self, prompt: str) -> Dict[str, Any]:
        """Provides a safe deterministic plan if model output parsing fails."""
        prompt_lower = prompt.lower()
        if "inspection" in prompt_lower or "heat exchanger" in prompt_lower or "report" in prompt_lower:
            return {
                "task_type": "industrial_inspection_audit",
                "intent_summary": "Perform technical audit of refinery heat exchanger inspection report",
                "steps": [
                    {"step": 1, "action": "OCR scanned ultrasonic thickness report", "worker": "vision", "tool": "ocr", "depends_on": []},
                    {"step": 2, "action": "Retrieve MRPL SOP for Heat Exchangers", "worker": "document", "tool": "rag_search", "depends_on": []},
                    {"step": 3, "action": "API 510 corrosion rate & remaining life calculation", "worker": "coding", "tool": "sandbox_exec", "depends_on": [1, 2]},
                    {"step": 4, "action": "Synthesize engineering compliance findings", "worker": "general", "depends_on": [3]},
                    {"step": 5, "action": "Generate official refinery Approval Note (.docx)", "worker": "document", "tool": "doc_generate", "depends_on": [4]},
                ],
            }
        elif "efficiency" in prompt_lower or "spreadsheet" in prompt_lower:
            return {
                "task_type": "spreadsheet_efficiency_analysis",
                "intent_summary": "Analyze unit sensor log and evaluate thermodynamic efficiency",
                "steps": [
                    {"step": 1, "action": "Parse sensor log spreadsheet", "worker": "document", "tool": "spreadsheet_read", "depends_on": []},
                    {"step": 2, "action": "Compute heat duty & thermal efficiency in sandbox", "worker": "coding", "tool": "sandbox_exec", "depends_on": [1]},
                    {"step": 3, "action": "Generate efficiency report balance sheet (.xlsx)", "worker": "document", "tool": "doc_generate", "depends_on": [2]},
                ],
            }
        elif "p&id" in prompt_lower or "valve" in prompt_lower:
            return {
                "task_type": "pid_diagram_verification",
                "intent_summary": "Verify P&ID diagram valves and interlocks against safety standards",
                "steps": [
                    {"step": 1, "action": "Inspect P&ID topology and safety relief valves", "worker": "vision", "tool": "vision_analyze", "depends_on": []},
                    {"step": 2, "action": "Cross-reference safety interlock SOP", "worker": "document", "tool": "rag_search", "depends_on": []},
                    {"step": 3, "action": "Synthesize safety verification summary", "worker": "general", "depends_on": [1, 2]},
                ],
            }
        else:
            return {
                "task_type": "standard_industrial_inquiry",
                "intent_summary": "Query local sovereign documentation and formulate response",
                "steps": [
                    {"step": 1, "action": "Search refinery knowledge base", "worker": "document", "tool": "rag_search", "depends_on": []},
                    {"step": 2, "action": "Synthesize verified engineering response", "worker": "general", "depends_on": [1]},
                ],
            }


ORGANIZER = OrganizerService()
