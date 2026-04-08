import pytest
from unittest.mock import patch
from app.models.agent import Agent


@pytest.mark.asyncio
async def test_list_threads_empty(client):
    resp = await client.get("/api/threads")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_thread(client, db_session):
    agent = Agent(
        id="writer", name="Writer", role="Scriptwriter",
        file_path="agents/writer.md", system_prompt="Write scripts.",
        avatar_color="#3b82f6", department="content",
    )
    db_session.add(agent)
    await db_session.commit()

    with patch("app.routers.threads._process_agent_response"):
        resp = await client.post("/api/threads", json={
            "subject": "Test Thread",
            "recipient_agent_ids": ["writer"],
            "content": "Hello writer!",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["subject"] == "Test Thread"
    assert "writer" in data["participants"]


@pytest.mark.asyncio
async def test_create_thread_invalid_agent(client):
    resp = await client.post("/api/threads", json={
        "subject": "Bad Thread",
        "recipient_agent_ids": ["nonexistent"],
        "content": "Hello?",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_thread_not_found(client):
    resp = await client.get("/api/threads/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_thread_with_messages(client, db_session):
    agent = Agent(
        id="reader", name="Reader", role="Analyst",
        file_path="agents/reader.md", system_prompt="Analyze.",
        avatar_color="#10b981", department="analytics",
    )
    db_session.add(agent)
    await db_session.commit()

    with patch("app.routers.threads._process_agent_response"):
        create_resp = await client.post("/api/threads", json={
            "subject": "Readable Thread",
            "recipient_agent_ids": ["reader"],
            "content": "Analyze this!",
        })
    thread_id = create_resp.json()["id"]

    resp = await client.get(f"/api/threads/{thread_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["subject"] == "Readable Thread"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "Analyze this!"
    assert data["messages"][0]["sender_type"] == "user"


@pytest.mark.asyncio
async def test_send_message_to_thread(client, db_session):
    agent = Agent(
        id="responder", name="Responder", role="Helper",
        file_path="agents/responder.md", system_prompt="Help.",
        avatar_color="#f59e0b", department="operations",
    )
    db_session.add(agent)
    await db_session.commit()

    with patch("app.routers.threads._process_agent_response"):
        create_resp = await client.post("/api/threads", json={
            "subject": "Convo Thread",
            "recipient_agent_ids": ["responder"],
            "content": "First message",
        })
    thread_id = create_resp.json()["id"]

    with patch("app.routers.threads._process_agent_response"):
        resp = await client.post(f"/api/threads/{thread_id}/messages", json={
            "content": "Follow up message",
        })
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"

    # Verify both messages are in the thread
    thread_resp = await client.get(f"/api/threads/{thread_id}")
    assert len(thread_resp.json()["messages"]) == 2
