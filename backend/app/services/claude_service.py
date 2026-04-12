from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOOL_ROUNDS
from app.models.tool import ToolCall
from app.models.memory import AgentMemory
from app.tools import get_tool, tools_to_claude_schema


@dataclass
class AgentResponse:
    text: str
    tool_calls: list[dict] = field(default_factory=list)


def get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


def format_thread_for_agent(messages: list[dict], agent_id: str) -> list[dict]:
    """Format thread messages into Claude conversation format.

    The current agent's prior messages become 'assistant' role.
    All other messages (user + other agents) become 'user' role with sender labels.
    """
    formatted = []
    for msg in messages:
        if msg["sender_type"] == "agent" and msg.get("sender_agent_id") == agent_id:
            formatted.append({"role": "assistant", "content": msg["content"]})
        else:
            if msg["sender_type"] == "user":
                label = "CEO (You — the human operator)"
            else:
                label = msg.get("sender_name", msg.get("sender_agent_id", "Unknown Agent"))
            formatted.append({
                "role": "user",
                "content": f"[From: {label}]\n{msg['content']}",
            })

    # Ensure conversation starts with user role
    if formatted and formatted[0]["role"] == "assistant":
        formatted.insert(0, {"role": "user", "content": "[System] You have been added to this thread."})

    # Merge consecutive same-role messages
    merged = []
    for msg in formatted:
        if merged and merged[-1]["role"] == msg["role"]:
            merged[-1]["content"] += "\n\n" + msg["content"]
        else:
            merged.append(msg)

    return merged if merged else [{"role": "user", "content": "[System] New thread started."}]


async def _get_agent_memories(agent_id: str, db: AsyncSession, limit: int = 20) -> list[AgentMemory]:
    """Fetch recent memories for an agent to inject into system prompt."""
    result = await db.execute(
        select(AgentMemory)
        .where(AgentMemory.agent_id == agent_id)
        .order_by(AgentMemory.updated_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


def _build_system_prompt(base_prompt: str, has_tools: bool, memories: list[AgentMemory]) -> str:
    """Build the full system prompt with tool context and memories."""
    prompt = base_prompt

    if has_tools:
        prompt += "\n\n## Tool Usage\nYou have access to tools that allow you to take real actions. When asked to do something actionable (create tasks, generate reports, send notifications, create invoices, etc.), use the appropriate tool rather than just describing what you would do. After using tools, summarize what you did and the results."

    if memories:
        prompt += "\n\n## Your Memory\nHere are things you've previously noted:\n"
        for m in memories:
            prompt += f"- [{m.memory_type}] {m.key}: {json.dumps(m.value)}\n"

    return prompt


async def _execute_tool(
    tool_name: str,
    tool_input: dict,
    agent_id: str,
    thread_id: str | None,
    db: AsyncSession,
) -> tuple[dict, str]:
    """Execute a tool and return (result_dict, tool_call_id)."""
    handler = get_tool(tool_name)
    tool_call_id = str(uuid.uuid4())

    tool_call_record = ToolCall(
        id=tool_call_id,
        thread_id=thread_id,
        agent_id=agent_id,
        tool_id=tool_name,
        tool_name=handler.name if handler else tool_name,
        input_data=tool_input,
        status="executing",
        started_at=datetime.now(timezone.utc),
    )
    db.add(tool_call_record)
    await db.flush()

    if not handler:
        tool_call_record.status = "failed"
        tool_call_record.error_message = f"Tool '{tool_name}' not found"
        tool_call_record.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return {"error": f"Tool '{tool_name}' not found"}, tool_call_id

    try:
        result = await handler.handler(
            **tool_input,
            agent_id=agent_id,
            db=db,
            thread_id=thread_id,
        )
        tool_call_record.output_data = result
        tool_call_record.status = "completed"
        tool_call_record.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return result, tool_call_id
    except Exception as e:
        tool_call_record.status = "failed"
        tool_call_record.error_message = str(e)[:500]
        tool_call_record.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return {"error": str(e)[:500]}, tool_call_id


async def generate_agent_response(
    system_prompt: str,
    thread_messages: list[dict],
    agent_id: str,
    agent_tools: list[str] | None = None,
    thread_id: str | None = None,
    db: AsyncSession | None = None,
) -> AgentResponse:
    """Generate a response from an agent using Claude, with optional tool use."""
    client = get_client()
    messages = format_thread_for_agent(thread_messages, agent_id)

    # Build tool schemas for Claude
    claude_tools = []
    if agent_tools:
        claude_tools = tools_to_claude_schema(agent_tools)

    # Get memories and build full system prompt
    memories = []
    if db:
        memories = await _get_agent_memories(agent_id, db)

    full_system_prompt = _build_system_prompt(
        system_prompt,
        has_tools=bool(claude_tools),
        memories=memories,
    )

    all_tool_calls = []

    for _round in range(MAX_TOOL_ROUNDS):
        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "system": full_system_prompt,
            "messages": messages,
        }
        if claude_tools:
            kwargs["tools"] = claude_tools

        response = await client.messages.create(**kwargs)

        # Collect text and tool_use blocks
        text_parts = []
        tool_uses = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        # If no tool calls or end_turn, we're done
        if response.stop_reason == "end_turn" or not tool_uses:
            return AgentResponse(
                text="\n".join(text_parts) if text_parts else "",
                tool_calls=all_tool_calls,
            )

        # Execute tools and build tool_result messages
        tool_results = []
        for tu in tool_uses:
            result, tc_id = await _execute_tool(
                tool_name=tu.name,
                tool_input=tu.input,
                agent_id=agent_id,
                thread_id=thread_id,
                db=db,
            )
            all_tool_calls.append({
                "tool_call_id": tc_id,
                "tool_name": tu.name,
                "input": tu.input,
                "output": result,
                "status": "completed" if "error" not in result else "failed",
            })

            # Truncate result for Claude context
            result_str = json.dumps(result)
            if len(result_str) > 4000:
                result_str = result_str[:4000] + '... (truncated)"}'

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": result_str,
            })

        # Append assistant message (with tool_use blocks) and tool results for next iteration
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # If we exceeded max rounds, return what we have
    final_text = "\n".join(text_parts) if text_parts else "I've completed the requested actions."
    return AgentResponse(text=final_text, tool_calls=all_tool_calls)


async def analyze_routing(
    agent_name: str,
    agent_role: str,
    response_text: str,
    reports_to: str | None,
    direct_reports: list[str],
    collaborates_with: list[str],
    all_agent_names: dict[str, str],
) -> list[str]:
    """Analyze an agent's response to determine routing.

    Returns list of agent IDs that should respond next.
    """
    client = get_client()

    agent_list = "\n".join(f"- {aid}: {aname}" for aid, aname in all_agent_names.items())

    prompt = f"""Analyze this message from {agent_name} ({agent_role}) and determine if any other agents should be notified to respond.

The agent's organizational relationships:
- Reports to: {reports_to or 'None (top of hierarchy)'}
- Direct reports: {', '.join(direct_reports) if direct_reports else 'None'}
- Collaborates with: {', '.join(collaborates_with) if collaborates_with else 'None'}

All available agents:
{agent_list}

The agent's message:
{response_text[:1000]}

Return ONLY a JSON object with:
- "route_to": list of agent IDs that should respond (empty list if none)
- "reason": brief explanation

Only route to agents when the message explicitly delegates, asks for input, or escalates. Do not route for general statements. Be conservative — route to at most 2 agents."""

    try:
        resp = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text
        # Extract JSON from response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            return [aid for aid in data.get("route_to", []) if aid in all_agent_names]
    except Exception:
        pass
    return []
