# YouTube Empire

Multi-agent communication platform for managing a YouTube content empire. 30 AI agents organized into departments (Executive, Content, Operations, Analytics, Monetization, Admin) collaborate through threaded conversations powered by Claude.

## Architecture

```
agents/     → 30 agent prompt definitions (Markdown + frontmatter)
backend/    → FastAPI + SQLAlchemy + Anthropic SDK
frontend/   → Next.js 16 + React 19 + Tailwind CSS 4
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Environment setup

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Docs at `/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Docker (alternative)

```bash
docker compose up --build
```

This starts both services. Frontend at `:3000`, API at `:8000`.

## Agent Organization

| Department    | Agents |
|---------------|--------|
| Executive     | CEO, Reflection Council, Secretary |
| Content       | Content VP, 3 Channel Managers, Scriptwriter, Hook Specialist, Storyteller, Shorts/Clips, Social Media Manager |
| Operations    | Operations VP, Project Manager, Video Editor, QA Lead, Thumbnail Designer, Workflow Orchestrator |
| Analytics     | Analytics VP, Data Analyst, Trend Researcher, SEO Specialist, Senior Researcher |
| Monetization  | Monetization VP, Partnership Manager, Affiliate Coordinator, Digital Product Manager, Newsletter Strategist, Community Manager |
| Admin         | Compliance Officer |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/{id}` | Agent details |
| GET | `/api/agents/org/tree` | Org chart data |
| GET | `/api/threads` | List threads |
| GET | `/api/threads/{id}` | Thread with messages |
| POST | `/api/threads` | Create thread |
| POST | `/api/threads/{id}/messages` | Send message |
