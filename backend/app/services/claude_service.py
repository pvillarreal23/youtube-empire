from __future__ import annotations

import anthropic
from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


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


def generate_agent_response(
    system_prompt: str,
    thread_messages: list[dict],
    agent_id: str,
) -> str:
    """Generate a response from an agent using Claude."""
    client = get_client()
    messages = format_thread_for_agent(thread_messages, agent_id)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def analyze_routing(
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
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
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
