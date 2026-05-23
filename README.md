# CopilotKit + Pydantic AI Chat App

L2 notebook app: a React/CopilotKit chat UI talking to two Pydantic AI agents
(OpenAI gpt-4.1 and Anthropic claude-haiku-4-5) over the AG-UI protocol.

## Setup

1. Install Python deps (creates `.venv`):
   ```bash
   uv sync
   ```
2. Install Node deps:
   ```bash
   npm install
   npm --prefix frontend install
   ```
3. Add API keys:
   ```bash
   cp .env-template .env
   # edit .env and set OPENAI_API_KEY and ANTHROPIC_API_KEY
   ```

## Run

```bash
npm run dev
```

Starts three processes:
- Backend (FastAPI agents) — http://localhost:8002
- CopilotRuntime — http://localhost:4002
- Frontend (Vite) — http://localhost:3002

Open http://localhost:3002 and chat. Use the dropdown to switch between OpenAI and Claude.

## Ports

| Process | Port |
|---------|------|
| Python agents (FastAPI) | 8002 |
| CopilotRuntime (Node)   | 4002 |
| Frontend (Vite)         | 3002 |
