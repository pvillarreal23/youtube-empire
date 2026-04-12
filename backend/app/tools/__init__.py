"""Tool registry for the agentic AI framework.

Tools are registered via the @tool decorator and stored in an in-memory registry.
At startup, registered tools are synced to the database for persistence and querying.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

_registry: dict[str, "ToolHandler"] = {}


@dataclass
class ToolHandler:
    id: str
    name: str
    description: str
    category: str
    input_schema: dict
    handler: Callable
    requires_approval: bool = False


def register_tool(handler: ToolHandler) -> None:
    _registry[handler.id] = handler


def get_tool(tool_id: str) -> ToolHandler | None:
    return _registry.get(tool_id)


def get_tools_for_agent(agent_tool_ids: list[str]) -> list[ToolHandler]:
    return [_registry[tid] for tid in agent_tool_ids if tid in _registry]


def get_all_tools() -> list[ToolHandler]:
    return list(_registry.values())


def tools_to_claude_schema(tool_ids: list[str]) -> list[dict[str, Any]]:
    """Convert tool handlers to Claude API tool format."""
    schemas = []
    for tid in tool_ids:
        handler = _registry.get(tid)
        if handler:
            schemas.append({
                "name": handler.id,
                "description": handler.description,
                "input_schema": handler.input_schema,
            })
    return schemas
