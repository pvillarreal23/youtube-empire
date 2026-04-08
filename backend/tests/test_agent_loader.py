from app.services.agent_loader import slugify, parse_agents


def test_slugify():
    assert slugify("CEO Agent") == "ceo-agent"
    assert slugify("AI & Tech Channel Manager") == "ai-and-tech-channel-manager"
    assert slugify("  Some  Spaces  ") == "some-spaces"


def test_parse_agents_returns_all():
    agents = parse_agents()
    assert len(agents) == 30
    ids = {a["id"] for a in agents}
    assert "ceo-agent" in ids
    assert "scriptwriter-agent" in ids


def test_parse_agents_have_required_fields():
    agents = parse_agents()
    for agent in agents:
        assert agent["id"]
        assert agent["name"]
        assert agent["system_prompt"]
        assert agent["file_path"]
        assert agent["department"]
        assert agent["avatar_color"]
