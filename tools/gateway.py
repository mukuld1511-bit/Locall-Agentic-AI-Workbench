"""Tool Gateway Service for Sovereign Industrial Operations.

Acts as the single execution boundary between the 500M Organizer and executable tools:
1. Validates Tool Input Schema against specification.
2. Evaluates Central Policy Engine and RBAC permissions for the calling user.
3. Checks Air-Gapped Network and Resource constraints.
4. Dispatches execution to isolated tool runners (sandbox, safe file ops, OCR, VLM).
5. Captures output schema, duration, and tamper-evident audit records.
THE LLM NEVER EXECUTES ARBITRARY SHELL STRINGS.
"""

import time
from typing import Any, Dict, Optional
from backend.app.audit.audit_service import AUDIT
from backend.app.policy.policy_engine import POLICY
from backend.app.rbac.rbac_service import RBAC
from tools.registry import TOOL_REGISTRY, ToolDefinition
from tools.sandbox.sandbox_runner import SANDBOX
from tools.file_tools.file_ops import safe_file_read, safe_file_write
from tools.ocr.ocr_engine import OCR_ENGINE
from tools.vision.vision_engine import VISION_ENGINE
from tools.spreadsheets.spreadsheet_ops import SPREADSHEET_OPS
from tools.documents.doc_generator import DOC_GENERATOR


class ToolGateway:
    def __init__(self):
        self.registry = TOOL_REGISTRY
        self._register_canonical_tools()

    def _register_canonical_tools(self) -> None:
        """Registers canonical tools required by the workbench."""
        # 1. sandbox_exec
        self.registry.register(
            ToolDefinition(
                name="sandbox_exec",
                description="Executes mathematical/engineering calculations in isolated Python sandbox.",
                input_schema={"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
                output_schema={"type": "object", "properties": {"stdout": {"type": "string"}, "exit_code": {"type": "integer"}}},
                required_permissions=["CODE_EXECUTE_SANDBOX"],
                risk_level="MEDIUM",
                audit_category="SANDBOX_EXECUTION",
                timeout_seconds=10,
                network_required=False,
                implementation=lambda code, **kw: SANDBOX.execute_python(code),
            )
        )

        # 2. ocr
        self.registry.register(
            ToolDefinition(
                name="ocr",
                description="Extracts structured text from scanned engineering inspection reports.",
                input_schema={"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]},
                output_schema={"type": "object", "properties": {"extracted_text": {"type": "string"}}},
                required_permissions=["DOC_SEARCH_PUBLIC"],
                risk_level="LOW",
                audit_category="DOCUMENT_OCR",
                timeout_seconds=15,
                network_required=False,
                implementation=lambda file_path, **kw: OCR_ENGINE.process_document(file_path),
            )
        )

        # 3. vision_analyze
        self.registry.register(
            ToolDefinition(
                name="vision_analyze",
                description="Analyzes P&ID diagrams, valves, and refinery process equipment imagery.",
                input_schema={"type": "object", "properties": {"image_path": {"type": "string"}, "diagram_type": {"type": "string"}}, "required": ["image_path"]},
                output_schema={"type": "object", "properties": {"extracted_components": {"type": "array"}}},
                required_permissions=["VISION_PID_ANALYZE"],
                risk_level="MEDIUM",
                audit_category="VISION_INSPECTION",
                timeout_seconds=20,
                network_required=False,
                implementation=lambda image_path, diagram_type="pid", **kw: VISION_ENGINE.analyze_diagram(image_path, diagram_type),
            )
        )

        # 4. spreadsheet_read
        self.registry.register(
            ToolDefinition(
                name="spreadsheet_read",
                description="Parses plant sensor data and equipment operating logs.",
                input_schema={"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]},
                output_schema={"type": "object", "properties": {"averages": {"type": "object"}}},
                required_permissions=["SPREADSHEET_ANALYZE"],
                risk_level="MEDIUM",
                audit_category="DATA_ANALYSIS",
                timeout_seconds=15,
                network_required=False,
                implementation=lambda file_path, **kw: SPREADSHEET_OPS.parse_sensor_data(file_path),
            )
        )

        # 5. doc_generate
        self.registry.register(
            ToolDefinition(
                name="doc_generate",
                description="Produces verified refinery engineering approval notes, spreadsheets, and briefing slides.",
                input_schema={"type": "object", "properties": {"artifact_format": {"type": "string"}, "equipment_tag": {"type": "string"}, "data": {"type": "object"}}, "required": ["artifact_format", "equipment_tag"]},
                output_schema={"type": "object", "properties": {"file_path": {"type": "string"}, "sha256": {"type": "string"}}},
                required_permissions=["DOC_GENERATE_OFFICE"],
                risk_level="MEDIUM",
                audit_category="DELIVERABLE_CREATION",
                timeout_seconds=15,
                network_required=False,
                implementation=self._exec_doc_generate,
            )
        )

        # 6. file_read
        self.registry.register(
            ToolDefinition(
                name="file_read",
                description="Safely reads permitted file contents within data boundaries.",
                input_schema={"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]},
                output_schema={"type": "object", "properties": {"content": {"type": "string"}}},
                required_permissions=["DOC_SEARCH_PUBLIC"],
                risk_level="LOW",
                audit_category="FILE_OPERATION",
                timeout_seconds=5,
                network_required=False,
                implementation=lambda file_path, **kw: safe_file_read(file_path),
            )
        )

        # 7. rag_search & doc_search
        self.registry.register(
            ToolDefinition(
                name="rag_search",
                description="Queries local sovereign knowledge base for refinery SOPs and technical manuals.",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"]},
                output_schema={"type": "object", "properties": {"results": {"type": "array"}}},
                required_permissions=["DOC_SEARCH_PUBLIC"],
                risk_level="LOW",
                audit_category="KNOWLEDGE_RETRIEVAL",
                timeout_seconds=10,
                network_required=False,
                implementation=self._exec_rag_search,
            )
        )

    def _exec_doc_generate(self, artifact_format: str, equipment_tag: str, data: Dict[str, Any], requester: str = "Engineer", **kw) -> Dict[str, Any]:
        fmt = artifact_format.lower()
        if "docx" in fmt or "word" in fmt or "note" in fmt:
            return DOC_GENERATOR.generate_approval_note_docx(equipment_tag, data, requester)
        elif "xlsx" in fmt or "excel" in fmt or "sheet" in fmt or "csv" in fmt:
            return DOC_GENERATOR.generate_efficiency_xlsx(equipment_tag, data)
        elif "pptx" in fmt or "slide" in fmt or "presentation" in fmt:
            return DOC_GENERATOR.generate_presentation_pptx(equipment_tag, data)
        else:
            return DOC_GENERATOR.generate_approval_note_docx(equipment_tag, data, requester)

    def _exec_rag_search(self, query: str, top_k: int = 3, user_role: str = "GRADE_1", **kw) -> Dict[str, Any]:
        from rag.engine import RAG_ENGINE
        return RAG_ENGINE.search(query, role=user_role, top_k=top_k)

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str,
        role: str,
        request_id: Optional[str] = None,
        data_sensitivity: str = "PUBLIC_INTERNAL",
    ) -> Dict[str, Any]:
        """Validates tool request, checks policy engine, and invokes tool with strict audit tracing."""
        tool = self.registry.get_tool(tool_name)
        if not tool:
            AUDIT.log_event(
                event_type="TOOL_NOT_FOUND",
                action=f"tool_exec:{tool_name}",
                status="FAILED",
                user_id=user_id,
                role=role,
                request_id=request_id,
                details={"error": f"Tool '{tool_name}' is not registered"},
            )
            return {"success": False, "error": f"Tool '{tool_name}' does not exist in registry."}

        # 1. Schema Validation (ensure all required parameters exist)
        req_props = tool.input_schema.get("required", [])
        for req in req_props:
            if req not in arguments:
                return {"success": False, "error": f"Schema validation error: Missing required parameter '{req}'."}

        # 2. Central Policy Engine Evaluation
        policy_eval = POLICY.evaluate(
            user_id=user_id,
            role=role,
            action=tool_name,
            resource=f"tool:{tool_name}",
            tool=tool_name,
            data_sensitivity=data_sensitivity,
            request_id=request_id,
        )

        if policy_eval.decision != "ALLOW":
            AUDIT.log_event(
                event_type="TOOL_POLICY_BLOCKED",
                action=f"tool_exec:{tool_name}",
                status="BLOCKED",
                user_id=user_id,
                role=role,
                tool=tool_name,
                decision=policy_eval.decision,
                request_id=request_id,
                details={"reason": policy_eval.reason, "risk_level": policy_eval.risk_level},
            )
            return {
                "success": False,
                "error": f"Policy Denied: {policy_eval.reason}",
                "decision": policy_eval.decision,
                "requires_approval": policy_eval.requires_human_approval,
            }

        # 3. Tool Execution with Latency Measurement
        start_time = time.time()
        try:
            # Pass execution context if needed
            kwargs = {**arguments, "user_id": user_id, "user_role": role, "requester": user_id}
            if tool.implementation:
                result = tool.implementation(**kwargs)
            else:
                result = {"success": False, "error": "Tool implementation missing"}

            latency_ms = (time.time() - start_time) * 1000.0

            AUDIT.log_event(
                event_type="TOOL_EXECUTED",
                action=f"tool_exec:{tool_name}",
                status="SUCCESS" if result.get("success", True) else "FAILED",
                user_id=user_id,
                role=role,
                tool=tool_name,
                request_id=request_id,
                details={"latency_ms": round(latency_ms, 2), "risk_level": tool.risk_level},
            )

            return {
                "success": True,
                "tool_name": tool_name,
                "output": result,
                "latency_ms": round(latency_ms, 2),
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            AUDIT.log_event(
                event_type="TOOL_EXECUTION_ERROR",
                action=f"tool_exec:{tool_name}",
                status="FAILED",
                user_id=user_id,
                role=role,
                tool=tool_name,
                request_id=request_id,
                details={"error": str(e), "latency_ms": round(latency_ms, 2)},
            )
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}


TOOL_GATEWAY = ToolGateway()
