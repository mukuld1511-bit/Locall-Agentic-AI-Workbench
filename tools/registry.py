"""Canonical Tool Registry & Schemas for Sovereign Industrial Operations.

Every tool exposed to the 500M Organizer MUST be registered here with:
- Strict JSON input/output schema
- Required RBAC permission
- Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
- Execution timeout and resource limits
- Audit categorization
Arbitrary shell execution is FORBIDDEN.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_permissions: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    audit_category: str
    timeout_seconds: int = 15
    network_required: bool = False
    implementation: Optional[Callable[..., Dict[str, Any]]] = None


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "required_permissions": t.required_permissions,
                "risk_level": t.risk_level,
                "network_required": t.network_required,
                "timeout_seconds": t.timeout_seconds,
            }
            for t in self._tools.values()
        ]


TOOL_REGISTRY = ToolRegistry()
