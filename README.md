# CopilotKit + Pydantic AI Chat App

L2 notebook app: a React/CopilotKit chat UI talking to three Pydantic AI agents
(OpenAI gpt-4.1, Anthropic claude-haiku-4-5, and an A2UI claude-sonnet-4-6 agent)
over the AG-UI protocol.

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

## Contracts

These values are shared across the language/process boundary and must stay in
sync — nothing enforces them at compile time, so changing one half silently
breaks the wiring.

### Agents

The agent is identified by three different names across the stack. The runtime
maps the UI `agentId` to a FastAPI route via `HttpAgent`.

| UI `agentId` (dropdown) | FastAPI route | Pydantic AI agent / model |
|-------------------------|---------------|---------------------------|
| `default`               | `/openai`     | `openai_agent` — `openai:gpt-4.1` |
| `claude`                | `/anthropic`  | `claude_agent` — `anthropic:claude-haiku-4-5` |
| `a2ui`                  | `/a2ui`       | `a2ui_agent` — `anthropic:claude-sonnet-4-6` |

Single sources of truth:
- **Frontend** (`agentId`s, labels, routes, A2UI scope): `frontend/src/agents.ts`
  — consumed by `App.tsx`, `server.ts`, and `use-example-suggestions.ts`.
- **Backend** (route → agent): `AGENT_ROUTES` in `backend/agents.py` — consumed
  by `backend/main.py`.

### Exact strings & invariants

| What | Value | Where it must match |
|------|-------|---------------------|
| Catalog id | `copilotkit://app-dashboard-catalog` | `backend/agents.py` `CATALOG_ID` ⇆ `frontend/src/catalog/index.ts` `CATALOG_ID` ⇆ the `catalogId` the agent passes to `render_a2ui` |
| A2UI tool-result key | `a2ui_operations` | `backend/a2ui.py` `render()` ⇆ what `@ag-ui/a2ui-middleware` detects |
| Surface id | `flight-search-results` | `backend/agents.py` `SURFACE_ID` (createSurface ⇆ updateComponents ⇆ updateDataModel) |
| A2UI middleware scope | `["a2ui"]` | `server.ts` `a2ui.agents` — **must** be scoped or `render_a2ui` is injected into every agent and breaks L2/L3 |
| Allowed component names | `COMPONENT_NAMES` | `backend/agents.py` prompt ⇆ keys of `demonstrationCatalogDefinitions` in `frontend/src/catalog/definitions.ts` |
| Vite proxy path | `/api/copilotkit` → `:4002` | `frontend/vite.config.ts` ⇆ `runtimeUrl` in `main.tsx` |
