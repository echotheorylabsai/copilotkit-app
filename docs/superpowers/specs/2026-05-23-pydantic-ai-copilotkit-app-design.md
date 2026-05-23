# Pydantic AI + CopilotKit Chat App — Design

**Date:** 2026-05-23
**Status:** Approved (design)

## Goal

Turn the DeepLearning.AI **L2 notebook** ("Building a Basic Agent UI") into a standalone,
runnable app in this repo. Keep the architecture and logic **as close to the notebook as
possible** — the *only* deliberate change is swapping the Python agent framework from
**LangGraph** to **Pydantic AI** (which natively supports the AG-UI protocol).

Non-goals: no extra features, no abstractions, no enhancements beyond what the notebook
shows. Minimal and faithful.

## Tooling constraints

- Python deps managed with **uv** (`pyproject.toml` + `.venv`), **not pip**.
- Three processes start with **one command** (`npm run dev` via `concurrently`).
- Two agent backends: **OpenAI gpt-4.1** (`default`) and **Anthropic claude-haiku-4-5**
  (`claude`) — swap chosen in the UI.

## Architecture

```
Python (uv venv) :8002          Node runtime :4002        Vite + React :3002
  POST /openai   -> gpt-4.1       CopilotRuntime            CopilotKit provider
  POST /anthropic-> claude-haiku    default -> /openai        + CopilotChat
  (FastAPI + AGUIAdapter)          claude  -> /anthropic     proxies /api/copilotkit -> :4002
        ^                                |   (HttpAgent)            |
        |________________ AG-UI HTTP ____|                         |
                                          <----- browser ----------|
```

Three processes, one `npm run dev`:
- **Backend** — `uv run uvicorn` FastAPI app, both agents as POST routes, `:8002`.
- **Runtime** — `tsx server.ts`, registers `default` + `claude` via generic `HttpAgent`, `:4002`.
- **Frontend** — Vite dev server `:3002`, proxies `/api/copilotkit` → `:4002`.

## File layout

```
copilotkit/
├── pyproject.toml          # uv: pydantic-ai-slim[ag-ui,openai,anthropic], fastapi,
│                           #     uvicorn, python-dotenv
├── package.json            # root: "dev" = concurrently(backend, runtime, frontend)
├── .env / .env.example     # OPENAI_API_KEY, ANTHROPIC_API_KEY (.env gitignored)
├── .gitignore
├── README.md               # how to install (uv sync, npm install) and run (npm run dev)
├── backend/
│   ├── main.py             # FastAPI app, loads .env, two POST routes via AGUIAdapter
│   └── agents.py           # openai_agent, claude_agent (pydantic_ai.Agent)
└── frontend/
    ├── server.ts           # CopilotRuntime: default + claude via HttpAgent
    ├── vite.config.ts      # proxy /api/copilotkit -> http://localhost:4002
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── main.tsx        # <CopilotKit runtimeUrl="/api/copilotkit"> provider
        └── App.tsx         # <CopilotChat agentId=...> + dropdown to switch default/claude
```

## Backend (the only real rewrite from the notebook)

`backend/agents.py`:
```python
from pydantic_ai import Agent

openai_agent = Agent("openai:gpt-4.1", system_prompt="You are a helpful assistant")
claude_agent = Agent("anthropic:claude-haiku-4-5", system_prompt="You are a helpful assistant")
```

`backend/main.py`:
```python
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from pydantic_ai.ui.ag_ui import AGUIAdapter
from agents import openai_agent, claude_agent

app = FastAPI()

@app.post("/openai")
async def openai_ep(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=openai_agent)

@app.post("/anthropic")
async def anthropic_ep(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=claude_agent)
```
Run: `uv run uvicorn backend.main:app --port 8002` (or `--reload` in dev).

**Verified against installed pydantic-ai 1.102.0:** `pydantic_ai.ui.ag_ui.AGUIAdapter`
exists with `dispatch_request`; `StateDeps`/`SSE_CONTENT_TYPE` live in `pydantic_ai.ui`.
`Agent.to_ag_ui()` exists but is deprecated — we use the recommended `AGUIAdapter`.

## Frontend `server.ts` (one import swap from the notebook)

```ts
import { serve } from "@hono/node-server";
import { HttpAgent } from "@ag-ui/client";          // was LangGraphHttpAgent
import { CopilotRuntime, createCopilotEndpoint } from "@copilotkit/runtime/v2";

const openaiAgent = new HttpAgent({ url: process.env.OPENAI_AGENT_URL || "http://localhost:8002/openai" });
const claudeAgent = new HttpAgent({ url: process.env.CLAUDE_AGENT_URL || "http://localhost:8002/anthropic" });

const runtime = new CopilotRuntime({ agents: { default: openaiAgent, claude: claudeAgent } });
const app = createCopilotEndpoint({ runtime, basePath: "/api/copilotkit" });

serve({ fetch: app.fetch, port: 4002 }, () =>
  console.log("CopilotKit API server running at http://localhost:4002"));
```

## Frontend React (unchanged from notebook, except agent switch)

- `main.tsx`: identical to the notebook — `<CopilotKit runtimeUrl="/api/copilotkit"
  useSingleEndpoint={false}>` wrapping `<App />`, importing v2 styles.
- `App.tsx`: `<CopilotChat agentId={agentId} />` plus a small dropdown that flips
  `agentId` between `"default"` (OpenAI) and `"claude"` (Anthropic). The switching state
  (~5–10 lines) is left as a user contribution.
- `vite.config.ts`: dev server on 3002, proxy `/api/copilotkit` → `http://localhost:4002`.

## Framework-inherent omissions (faithful, not enhancements)

| Notebook (LangGraph) | Pydantic AI | Reason |
|---|---|---|
| `MemorySaver()` checkpointer | none | AG-UI replays full message history each request; agent is stateless per turn |
| `CopilotKitMiddleware()` | none | Frontend-tool support is built into Pydantic AI's AG-UI adapter (used in L3) |

## Ports

| Process | Port | Notebook parity |
|---|---|---|
| Python agents (FastAPI) | 8002 | same |
| CopilotRuntime (Node) | 4002 | same |
| Frontend (Vite) | 3002 | same |

## Success criteria

1. `uv sync` creates `.venv` with all Python deps; `npm install` (root + frontend) succeeds.
2. `npm run dev` starts all three processes.
3. Browser at `:3002` shows `CopilotChat`; sending a message gets a streamed reply from OpenAI.
4. Switching the UI to `claude` routes to Anthropic and replies (given a valid `ANTHROPIC_API_KEY`).
5. No LangGraph dependency remains anywhere.

## Open risk

- `ANTHROPIC_API_KEY` must be a real billable API key from console.anthropic.com — a Claude
  Code/subscription login is not interchangeable. OpenAI path works independently.
```

