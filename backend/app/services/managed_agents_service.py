"""Service for dispatching agents to Anthropic's Managed Agents sandbox.

Allows individual agents to be dispatched as autonomous sandbox tasks
(e.g. research, trend analysis) while the main multi-agent orchestration
continues to run locally.
"""

from __future__ import annotations

import anthropic
from app.config import ANTHROPIC_API_KEY, MANAGED_AGENTS_MODEL


_BETA_HEADER = "managed-agents-2026-04-01"


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def create_managed_agent(
    name: str,
    system_prompt: str,
    model: str | None = None,
) -> dict:
    """Create a reusable managed agent on the Anthropic platform."""
    client = _get_client()
    agent = client.beta.agents.create(
        name=name,
        model=model or MANAGED_AGENTS_MODEL,
        system=system_prompt,
        tools=[{"type": "agent_toolset_20260401"}],
        betas=[_BETA_HEADER],
    )
    return {"id": agent.id, "name": agent.name, "model": agent.model}


def create_environment(name: str) -> dict:
    """Create a cloud sandbox environment for agent sessions."""
    client = _get_client()
    env = client.beta.environments.create(
        name=name,
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
        betas=[_BETA_HEADER],
    )
    return {"id": env.id, "name": env.name}


def start_session(
    managed_agent_id: str,
    environment_id: str,
    task: str,
) -> dict:
    """Start a managed agent session and send the initial task.

    Returns session info with the initial response events.
    """
    client = _get_client()

    session = client.beta.sessions.create(
        agent=managed_agent_id,
        environment_id=environment_id,
        betas=[_BETA_HEADER],
    )

    # Send the task as the first user message
    client.beta.sessions.events.send(
        session.id,
        events=[{
            "type": "user.message",
            "content": [{"type": "text", "text": task}],
        }],
        betas=[_BETA_HEADER],
    )

    return {
        "session_id": session.id,
        "status": "running",
    }


def get_session_events(session_id: str) -> list[dict]:
    """Retrieve all events from a managed agent session."""
    client = _get_client()

    events = client.beta.sessions.events.list(
        session_id,
        betas=[_BETA_HEADER],
    )

    result = []
    for event in events:
        entry = {"type": event.type}
        if hasattr(event, "content"):
            texts = []
            for block in event.content:
                if hasattr(block, "text"):
                    texts.append(block.text)
            if texts:
                entry["text"] = "\n".join(texts)
        result.append(entry)

    return result


def get_session_status(session_id: str) -> str:
    """Get the current status of a managed agent session."""
    client = _get_client()
    session = client.beta.sessions.retrieve(
        session_id,
        betas=[_BETA_HEADER],
    )
    return session.status


def dispatch_agent_task(
    agent_name: str,
    system_prompt: str,
    task: str,
) -> dict:
    """High-level helper: create agent + environment + session in one call.

    This is the main entry point for dispatching an agent to the sandbox.
    """
    # Create the managed agent
    agent_info = create_managed_agent(
        name=f"YT-Empire: {agent_name}",
        system_prompt=system_prompt,
    )

    # Create a sandbox environment
    env_info = create_environment(
        name=f"yt-empire-{agent_name.lower().replace(' ', '-')}",
    )

    # Start the session with the task
    session_info = start_session(
        managed_agent_id=agent_info["id"],
        environment_id=env_info["id"],
        task=task,
    )

    return {
        "managed_agent_id": agent_info["id"],
        "environment_id": env_info["id"],
        "session_id": session_info["session_id"],
        "status": session_info["status"],
    }
