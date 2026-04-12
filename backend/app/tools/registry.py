"""Decorator for registering functions as tools."""
from __future__ import annotations

from app.tools import ToolHandler, register_tool


def tool(
    id: str,
    name: str,
    description: str,
    category: str,
    input_schema: dict,
    requires_approval: bool = False,
):
    """Decorator to register an async function as an agent tool."""
    def decorator(func):
        handler = ToolHandler(
            id=id,
            name=name,
            description=description,
            category=category,
            input_schema=input_schema,
            handler=func,
            requires_approval=requires_approval,
        )
        register_tool(handler)
        return func
    return decorator
