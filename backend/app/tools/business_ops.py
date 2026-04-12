"""Business operations tools: invoices, knowledge base search."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_data import Invoice
from app.models.agent import Agent
from app.tools.registry import tool


@tool(
    id="create_invoice",
    name="Create Invoice",
    description="Create an invoice for a client (sponsorship, partnership, service, etc.). Returns the created invoice with its ID.",
    category="business_ops",
    input_schema={
        "type": "object",
        "properties": {
            "client_name": {"type": "string", "description": "Name of the client or company being invoiced"},
            "amount": {"type": "number", "description": "Invoice amount"},
            "currency": {"type": "string", "description": "Currency code (e.g., USD, EUR)", "default": "USD"},
            "description": {"type": "string", "description": "Description of what this invoice is for"},
            "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
        },
        "required": ["client_name", "amount", "description"],
    },
)
async def create_invoice(
    client_name: str,
    amount: float,
    description: str,
    currency: str = "USD",
    due_date: str | None = None,
    *,
    agent_id: str,
    db: AsyncSession,
    **kwargs,
) -> dict:
    invoice = Invoice(
        id=str(uuid.uuid4()),
        client_name=client_name,
        amount=amount,
        currency=currency,
        description=description,
        due_date=due_date,
        created_by_agent=agent_id,
    )
    db.add(invoice)
    await db.commit()
    return {
        "invoice_id": invoice.id,
        "client_name": invoice.client_name,
        "amount": invoice.amount,
        "currency": invoice.currency,
        "description": invoice.description,
        "due_date": invoice.due_date,
        "status": invoice.status,
        "message": f"Invoice created for {client_name}: {currency} {amount:.2f}",
    }


@tool(
    id="search_knowledge_base",
    name="Search Knowledge Base",
    description="Search the company knowledge base (agent definitions and stored information) for relevant information.",
    category="data_analytics",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "scope": {
                "type": "string",
                "enum": ["all", "agents"],
                "description": "Scope of search",
                "default": "all",
            },
        },
        "required": ["query"],
    },
)
async def search_knowledge_base(
    query: str,
    scope: str = "all",
    *,
    agent_id: str,
    db: AsyncSession,
    **kwargs,
) -> dict:
    query_lower = query.lower()
    results = []

    if scope in ("all", "agents"):
        agents_result = await db.execute(select(Agent))
        for agent in agents_result.scalars().all():
            # Search in agent name, role, and system prompt
            relevance = 0
            if query_lower in agent.name.lower():
                relevance += 3
            if query_lower in agent.role.lower():
                relevance += 2
            if query_lower in agent.system_prompt.lower():
                relevance += 1

            if relevance > 0:
                # Extract relevant snippet from system prompt
                prompt_lower = agent.system_prompt.lower()
                idx = prompt_lower.find(query_lower)
                snippet = ""
                if idx >= 0:
                    start = max(0, idx - 100)
                    end = min(len(agent.system_prompt), idx + len(query) + 200)
                    snippet = agent.system_prompt[start:end].strip()
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(agent.system_prompt):
                        snippet = snippet + "..."

                results.append({
                    "source": "agent",
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "role": agent.role,
                    "relevance": relevance,
                    "snippet": snippet or f"{agent.role} - {agent.name}",
                })

    results.sort(key=lambda x: x["relevance"], reverse=True)
    return {
        "query": query,
        "total_results": len(results),
        "results": results[:10],  # Top 10
    }
