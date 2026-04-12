"""Project management tools: tasks and status tracking."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_data import Task
from app.tools.registry import tool


@tool(
    id="create_task",
    name="Create Task",
    description="Create a tracked task or action item with assignment, deadline, priority, and project. Use this to formally assign work to team members.",
    category="project_mgmt",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short title for the task"},
            "description": {"type": "string", "description": "Detailed description of what needs to be done"},
            "assigned_to": {"type": "string", "description": "Agent ID to assign the task to (e.g., 'video-editor-agent')"},
            "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
            "priority": {
                "type": "string",
                "enum": ["P0", "P1", "P2", "P3"],
                "description": "Priority level: P0=critical, P1=high, P2=medium, P3=low",
                "default": "P2",
            },
            "project": {"type": "string", "description": "Project name or identifier (optional)"},
        },
        "required": ["title", "description", "assigned_to"],
    },
)
async def create_task(
    title: str,
    description: str,
    assigned_to: str,
    due_date: str | None = None,
    priority: str = "P2",
    project: str | None = None,
    *,
    agent_id: str,
    db: AsyncSession,
    **kwargs,
) -> dict:
    task = Task(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        assigned_to=assigned_to,
        due_date=due_date,
        priority=priority,
        project=project,
        created_by_agent=agent_id,
    )
    db.add(task)
    await db.commit()
    return {
        "task_id": task.id,
        "title": task.title,
        "assigned_to": task.assigned_to,
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date,
        "message": f"Task '{title}' created and assigned to {assigned_to}",
    }


@tool(
    id="update_task_status",
    name="Update Task Status",
    description="Update the status of an existing task. Use this to track progress on work items.",
    category="project_mgmt",
    input_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The ID of the task to update"},
            "new_status": {
                "type": "string",
                "enum": ["queued", "in_progress", "in_review", "blocked", "complete"],
                "description": "New status for the task",
            },
            "notes": {"type": "string", "description": "Optional notes about the status change"},
        },
        "required": ["task_id", "new_status"],
    },
)
async def update_task_status(
    task_id: str,
    new_status: str,
    notes: str | None = None,
    *,
    agent_id: str,
    db: AsyncSession,
    **kwargs,
) -> dict:
    task = await db.get(Task, task_id)
    if not task:
        return {"error": f"Task {task_id} not found", "success": False}

    old_status = task.status
    task.status = new_status
    task.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "task_id": task.id,
        "title": task.title,
        "old_status": old_status,
        "new_status": new_status,
        "notes": notes,
        "success": True,
        "message": f"Task '{task.title}' updated: {old_status} → {new_status}",
    }
