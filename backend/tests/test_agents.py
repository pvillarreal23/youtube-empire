import pytest
from app.models.agent import Agent


@pytest.mark.asyncio
async def test_list_agents_empty(client):
    resp = await client.get("/api/agents")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_agents_with_data(client, db_session):
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        file_path="agents/test.md",
        system_prompt="You are a test agent.",
        avatar_color="#8b5cf6",
        department="executive",
    )
    db_session.add(agent)
    await db_session.commit()

    resp = await client.get("/api/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "test-agent"
    assert data[0]["name"] == "Test Agent"


@pytest.mark.asyncio
async def test_get_agent_not_found(client):
    resp = await client.get("/api/agents/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_detail(client, db_session):
    agent = Agent(
        id="detail-agent",
        name="Detail Agent",
        role="Specialist",
        file_path="agents/detail.md",
        system_prompt="Detailed system prompt here.",
        avatar_color="#3b82f6",
        department="content",
    )
    db_session.add(agent)
    await db_session.commit()

    resp = await client.get("/api/agents/detail-agent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_prompt"] == "Detailed system prompt here."
    assert data["file_path"] == "agents/detail.md"


@pytest.mark.asyncio
async def test_org_tree(client, db_session):
    ceo = Agent(
        id="ceo", name="CEO", role="Chief", file_path="agents/ceo.md",
        system_prompt="CEO prompt", avatar_color="#8b5cf6", department="executive",
    )
    vp = Agent(
        id="vp-content", name="VP Content", role="VP", file_path="agents/vp.md",
        system_prompt="VP prompt", avatar_color="#3b82f6", department="content",
        reports_to="ceo",
    )
    db_session.add_all([ceo, vp])
    await db_session.commit()

    resp = await client.get("/api/agents/org/tree")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["edges"][0] == {"source": "ceo", "target": "vp-content"}
