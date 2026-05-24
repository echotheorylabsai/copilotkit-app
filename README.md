# CopilotKit + Pydantic AI Chat App

Demo app: a React/CopilotKit chat UI talking to five Pydantic AI agents
(OpenAI gpt-4.1, Anthropic claude-haiku-4-5, an A2UI claude-sonnet-4-6 agent, an
open-generative-UI claude-sonnet-4-6 agent, and a shared-state todo
claude-haiku-4-5 agent on its own `/todos` page) over the AG-UI protocol.

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

Open http://localhost:3002 and chat. Use the dropdown to switch agents: OpenAI and
Claude (plain chat), A2UI (declarative generative UI), and Open Gen UI (Excalidraw
MCP App + open-ended HTML/CSS/JS generative UI).

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
| `open`                  | `/open`       | `open_agent` — `anthropic:claude-sonnet-4-6` |
| `todo`                  | `/todos`      | `todo_agent` — `anthropic:claude-haiku-4-5` (on the `/todos` page, not the dropdown) |

Single sources of truth:
- **Frontend** (`agentId`s, labels, routes, A2UI + open-gen-UI scope flags):
  `frontend/src/agents.ts` — consumed by `App.tsx`, `server.ts`, and
  `use-example-suggestions.ts`. The `todo` agent carries `page: true`, which keeps it
  out of the chat dropdown (`DROPDOWN_AGENTS`) while still being wired into the
  runtime by `server.ts`.
- **Backend** (route → agent): `AGENT_ROUTES` in `backend/agents/__init__.py` —
  consumed by `backend/main.py`. Each agent lives in its own submodule:
  `backend/agents/openai.py`, `backend/agents/claude.py`, `backend/agents/a2ui.py`,
  `backend/agents/open_gen_ui.py`, `backend/agents/todos.py`. Routes needing
  request-scoped deps (the `todo` agent uses `StateDeps[TodoState]`) register a
  factory in `AGENT_DEPS`.

### Exact strings & invariants

| What | Value | Where it must match |
|------|-------|---------------------|
| Catalog id | `copilotkit://app-dashboard-catalog` | `backend/agents/a2ui.py` `CATALOG_ID` ⇆ `frontend/src/catalog/index.ts` `CATALOG_ID` ⇆ the `catalogId` the agent passes to `render_a2ui` |
| A2UI tool-result key | `a2ui_operations` | `backend/a2ui.py` `render()` ⇆ what `@ag-ui/a2ui-middleware` detects |
| Surface id | `flight-search-results` | `backend/agents/a2ui.py` `SURFACE_ID` (createSurface ⇆ updateComponents ⇆ updateDataModel) |
| A2UI middleware scope | `["a2ui"]` | `server.ts` `a2ui.agents` — **must** be scoped or `render_a2ui` is injected into every agent, breaking the plain-chat agents |
| Open-gen-UI / MCP-Apps scope | `["open"]` | `server.ts` `openGenerativeUI.agents` + each `mcpApps.servers[].agentId` — scoped so the Excalidraw MCP app and open generative UI are injected into the `open` agent only, leaving the other agents untouched |
| Allowed component names | `COMPONENT_NAMES` | `backend/agents/a2ui.py` prompt ⇆ keys of `demonstrationCatalogDefinitions` in `frontend/src/catalog/definitions.ts` |
| Vite proxy path | `/api/copilotkit` → `:4002` | `frontend/vite.config.ts` ⇆ `runtimeUrl` in `main.tsx` |
| Shared-state key | `todos` | `backend/agents/todos.py` `TodoState.todos` + the `StateSnapshotEvent` snapshot ⇆ `agent.state.todos` / `agent.setState({ todos })` in `frontend/src/TodoPage.tsx` |
| Shared-state frontend tool | `openOrCloseTodos` | `useFrontendTool` name in `frontend/src/TodoPage.tsx` ⇆ the tool name in the `todo_agent` system prompt (`backend/agents/todos.py`) |
