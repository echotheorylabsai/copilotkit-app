# Pydantic AI + CopilotKit Chat App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable chat app where a React/CopilotKit frontend talks to two Pydantic AI agents (OpenAI gpt-4.1 and Anthropic claude-haiku-4-5) over the AG-UI protocol, faithful to the L2 notebook with LangGraph swapped for Pydantic AI.

**Architecture:** A uv-managed FastAPI backend (`:8002`) exposes each agent as an AG-UI POST route via `AGUIAdapter.dispatch_request()`. A Node CopilotRuntime (`:4002`) registers both as generic `HttpAgent`s. A Vite/React frontend (`:3002`) renders `CopilotChat` and proxies `/api/copilotkit` to the runtime. `npm run dev` starts all three via `concurrently`.

**Tech Stack:** Python 3.12 + uv, pydantic-ai-slim[ag-ui,openai,anthropic], FastAPI, uvicorn, python-dotenv; Node 23 + TypeScript, @copilotkit/runtime v2, @ag-ui/client, @hono/node-server, tsx; React 18 + Vite, @copilotkit/react-core v2; concurrently.

**Testing note:** This is integration scaffolding, not algorithmic code. Verification = import checks, live `curl` against endpoints, and process startup — not unit tests. Keep it minimal.

---

## File Structure

```
copilotkit/
├── pyproject.toml          # uv project + Python deps
├── package.json            # root: concurrently dev orchestration
├── .env-template           # reference env vars (committed)
├── .gitignore              # ignores .env, .venv, node_modules, __pycache__
├── README.md               # install + run instructions
├── backend/
│   ├── __init__.py         # makes backend an importable package
│   ├── agents.py           # openai_agent, claude_agent
│   └── main.py             # FastAPI app + two AG-UI POST routes
└── frontend/
    ├── server.ts           # CopilotRuntime (default + claude via HttpAgent)
    ├── vite.config.ts       # dev server :3002 + proxy to :4002
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── tsconfig.node.json
    └── src/
        ├── main.tsx        # CopilotKit provider
        ├── App.tsx         # CopilotChat + agent-switch dropdown
        └── globals.css     # minimal layout (full-height)
```

---

## Task 1: Python project + dependencies via uv

**Files:**
- Create: `pyproject.toml`
- Create: `backend/__init__.py` (empty)

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "copilotkit-pydantic-ai-app"
version = "0.1.0"
description = "L2 notebook app: CopilotKit + Pydantic AI agents over AG-UI"
requires-python = ">=3.12"
dependencies = [
    "pydantic-ai-slim[ag-ui,openai,anthropic]>=1.102.0",
    "fastapi>=0.115",
    "uvicorn>=0.34",
    "python-dotenv>=1.0",
]

[tool.uv]
package = false
```

- [ ] **Step 2: Create empty `backend/__init__.py`**

```python
```

- [ ] **Step 3: Sync the environment**

Run: `uv sync`
Expected: creates `.venv/` and `uv.lock`, installs pydantic-ai, fastapi, uvicorn, python-dotenv without error.

- [ ] **Step 4: Verify key imports resolve**

Run:
```bash
uv run python -c "from pydantic_ai import Agent; from pydantic_ai.ui.ag_ui import AGUIAdapter; print('ok', hasattr(AGUIAdapter,'dispatch_request'))"
```
Expected: `ok True`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock backend/__init__.py
git commit -m "feat: uv project with pydantic-ai, fastapi deps"
```

---

## Task 2: Backend agents

**Files:**
- Create: `backend/agents.py`

- [ ] **Step 1: Write `backend/agents.py`**

```python
from pydantic_ai import Agent

# Mirrors the notebook's two create_agent() calls — same system prompt, Pydantic AI style.
openai_agent = Agent("openai:gpt-4.1", system_prompt="You are a helpful assistant")
claude_agent = Agent("anthropic:claude-haiku-4-5", system_prompt="You are a helpful assistant")
```

- [ ] **Step 2: Verify the module imports (no API call, just construction)**

Run: `uv run python -c "from backend.agents import openai_agent, claude_agent; print('agents ok')"`
Expected: `agents ok` (agent construction does not require an API key).

- [ ] **Step 3: Commit**

```bash
git add backend/agents.py
git commit -m "feat: define openai and claude pydantic-ai agents"
```

---

## Task 3: Backend FastAPI app with AG-UI routes

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: Write `backend/main.py`**

```python
from dotenv import load_dotenv

load_dotenv()  # load OPENAI_API_KEY / ANTHROPIC_API_KEY from .env

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from pydantic_ai.ui.ag_ui import AGUIAdapter

from backend.agents import openai_agent, claude_agent

app = FastAPI()


@app.post("/openai")
async def openai_endpoint(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=openai_agent)


@app.post("/anthropic")
async def anthropic_endpoint(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=claude_agent)
```

- [ ] **Step 2: Verify the app imports and routes are registered**

Run:
```bash
uv run python -c "from backend.main import app; print(sorted({r.path for r in app.routes if r.path in ('/openai','/anthropic')}))"
```
Expected: `['/anthropic', '/openai']`

- [ ] **Step 3: Verify the server boots (no API key needed to start)**

Run:
```bash
uv run uvicorn backend.main:app --port 8002 &
sleep 3
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8002/openai -H "Content-Type: application/json" -d '{}'
kill %1
```
Expected: a non-000 HTTP status (e.g. 4xx for an empty/invalid AG-UI body) — proves the route is live and parsing requests. (A full streamed reply needs a real key and is verified in Task 8.)

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat: FastAPI app exposing both agents over AG-UI"
```

---

## Task 4: Env template + gitignore

**Files:**
- Create: `.env-template`
- Modify: `.gitignore` (verify contents; created during brainstorming)

- [ ] **Step 1: Write `.env-template`**

```bash
# Copy this file to .env and fill in real keys. .env is gitignored.
# OpenAI key: https://platform.openai.com/api-keys
OPENAI_API_KEY=

# Anthropic key (must be a real API key sk-ant-... from console.anthropic.com,
# NOT a Claude Code subscription login): https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=
```

- [ ] **Step 2: Ensure `.gitignore` covers secrets and build artifacts**

Confirm `.gitignore` contains exactly these lines (overwrite if missing any):
```
.venv/
node_modules/
.env
__pycache__/
```

- [ ] **Step 3: Verify `.env` is ignored but `.env-template` is tracked**

Run: `touch .env && git check-ignore .env && git check-ignore -v .env-template; echo "exit=$?"`
Expected: prints `.env` (it is ignored); `.env-template` produces no output and `exit=1` (NOT ignored).

- [ ] **Step 4: Commit**

```bash
git add .env-template .gitignore
git commit -m "chore: add .env-template and confirm gitignore for secrets"
```

---

## Task 5: Frontend scaffold (package.json, tsconfig, vite, index.html)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`

- [ ] **Step 1: Write `frontend/package.json`**

```json
{
  "name": "frontend",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --port 3002",
    "runtime": "tsx server.ts",
    "build": "vite build"
  },
  "dependencies": {
    "@ag-ui/client": "^0.0.39",
    "@copilotkit/react-core": "^1.50.0",
    "@copilotkit/runtime": "^1.50.0",
    "@hono/node-server": "^1.13.7",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "tsx": "^4.19.2",
    "typescript": "^5.7.2",
    "vite": "^6.0.3"
  }
}
```

> Note for implementer: install with `npm install` in `frontend/`. If npm resolves newer compatible majors for `@copilotkit/*` or `@ag-ui/client`, accept the latest that still exports the `/v2` paths and `HttpAgent`; do not pin below the versions above. Verify imports in Task 6/7 still resolve after install.

- [ ] **Step 2: Write `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src", "server.ts"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: Write `frontend/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Write `frontend/vite.config.ts`**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3002,
    proxy: {
      "/api/copilotkit": "http://localhost:4002",
    },
  },
});
```

- [ ] **Step 5: Write `frontend/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CopilotKit + Pydantic AI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Install frontend dependencies**

Run: `cd frontend && npm install`
Expected: `node_modules/` created, no fatal peer-dependency errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/tsconfig.json frontend/tsconfig.node.json frontend/vite.config.ts frontend/index.html
git commit -m "feat: frontend scaffold (vite, tsconfig, package.json)"
```

---

## Task 6: Frontend React app (provider, chat, dropdown, styles)

**Files:**
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/globals.css`

- [ ] **Step 1: Write `frontend/src/globals.css`**

```css
html, body, #root {
  height: 100%;
  margin: 0;
}
.agent-switch {
  position: absolute;
  top: 12px;
  right: 16px;
  z-index: 10;
  font-size: 14px;
}
```

- [ ] **Step 2: Write `frontend/src/main.tsx` (identical pattern to the notebook)**

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <main className="h-screen w-screen">
      <CopilotKit runtimeUrl="/api/copilotkit" useSingleEndpoint={false}>
        <App />
      </CopilotKit>
    </main>
  </StrictMode>,
);
```

- [ ] **Step 3: Write `frontend/src/App.tsx` (CopilotChat + agent-switch dropdown)**

```tsx
import { useState } from "react";
import { CopilotChat } from "@copilotkit/react-core/v2";

// "default" -> OpenAI gpt-4.1, "claude" -> Anthropic claude-haiku-4-5
type AgentId = "default" | "claude";

export default function App() {
  const [agentId, setAgentId] = useState<AgentId>("default");

  return (
    <div style={{ height: "100%", position: "relative" }}>
      <select
        className="agent-switch"
        value={agentId}
        onChange={(e) => setAgentId(e.target.value as AgentId)}
      >
        <option value="default">OpenAI (gpt-4.1)</option>
        <option value="claude">Claude (haiku-4-5)</option>
      </select>
      <CopilotChat key={agentId} agentId={agentId} />
    </div>
  );
}
```

> Note for implementer: `key={agentId}` forces `CopilotChat` to remount on switch so it binds to the newly selected agent and starts a clean thread.

- [ ] **Step 4: Type-check the frontend**

Run: `cd frontend && npx tsc --noEmit`
Expected: no type errors. (If `@copilotkit/react-core/v2` types are missing for `CopilotChat`/`CopilotKit`, confirm the installed version exposes the `/v2` entry point; adjust import to the version's documented v2 path.)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/main.tsx frontend/src/App.tsx frontend/src/globals.css
git commit -m "feat: React app with CopilotChat and agent switcher"
```

---

## Task 7: CopilotRuntime server

**Files:**
- Create: `frontend/server.ts`

- [ ] **Step 1: Write `frontend/server.ts`**

```ts
import { serve } from "@hono/node-server";
import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime, createCopilotEndpoint } from "@copilotkit/runtime/v2";

const openaiAgent = new HttpAgent({
  url: process.env.OPENAI_AGENT_URL || "http://localhost:8002/openai",
});

const claudeAgent = new HttpAgent({
  url: process.env.CLAUDE_AGENT_URL || "http://localhost:8002/anthropic",
});

const runtime = new CopilotRuntime({
  agents: {
    default: openaiAgent,
    claude: claudeAgent,
  },
});

const app = createCopilotEndpoint({
  runtime,
  basePath: "/api/copilotkit",
});

serve({ fetch: app.fetch, port: 4002 }, () => {
  console.log("CopilotKit API server running at http://localhost:4002");
});
```

- [ ] **Step 2: Verify the runtime starts and serves the endpoint**

Run:
```bash
cd frontend && npx tsx server.ts &
sleep 3
curl -s -o /dev/null -w "%{http_code}" http://localhost:4002/api/copilotkit
kill %1
```
Expected: a non-000 HTTP status (the endpoint is reachable). Console prints the "running at http://localhost:4002" line.

- [ ] **Step 3: Commit**

```bash
git add frontend/server.ts
git commit -m "feat: CopilotRuntime registering both agents via HttpAgent"
```

---

## Task 8: One-command orchestration + README + end-to-end check

**Files:**
- Create: `package.json` (root)
- Create: `README.md`

- [ ] **Step 1: Write root `package.json`**

```json
{
  "name": "copilotkit-pydantic-ai-app",
  "private": true,
  "scripts": {
    "backend": "uv run uvicorn backend.main:app --port 8002 --reload",
    "runtime": "npm --prefix frontend run runtime",
    "frontend": "npm --prefix frontend run dev",
    "dev": "concurrently -n backend,runtime,frontend -c blue,magenta,green \"npm run backend\" \"npm run runtime\" \"npm run frontend\""
  },
  "devDependencies": {
    "concurrently": "^9.1.0"
  }
}
```

- [ ] **Step 2: Install root dev dependency**

Run: `npm install`
Expected: `concurrently` installed at repo root.

- [ ] **Step 3: Write `README.md`**

````markdown
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
````

- [ ] **Step 4: End-to-end smoke check (requires real keys in `.env`)**

Run: `npm run dev`, then in a browser open http://localhost:3002.
Expected:
- All three processes log startup with no errors.
- Sending "Hello chat!" streams a reply (OpenAI, `default`).
- Switching the dropdown to Claude and sending a message streams a reply from Anthropic.

(If keys are absent, processes still start; agent replies will error until keys are added. This is the documented Open Risk.)

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json README.md
git commit -m "feat: one-command dev orchestration and README"
```

---

## Self-Review

**Spec coverage:**
- uv venv, no pip → Task 1 ✓
- One command for 3 processes → Task 8 (`concurrently`) ✓
- OpenAI + Claude agents → Task 2 ✓
- AGUIAdapter.dispatch_request POST routes :8002 → Task 3 ✓
- Generic HttpAgent runtime default+claude :4002 → Task 7 ✓
- Notebook-identical provider/chat + switch dropdown :3002 → Tasks 5–6 ✓
- Vite proxy /api/copilotkit → :4002 → Task 5 ✓
- No MemorySaver / CopilotKitMiddleware (framework-inherent omission) → reflected by their absence in Tasks 2–3 ✓
- .env gitignored, .env-template committed → Task 4 ✓
- No LangGraph dependency anywhere → no task introduces it; pyproject (Task 1) and frontend deps (Task 5) exclude it ✓

**Placeholder scan:** No TBD/TODO; every code step contains complete content.

**Type consistency:** `AgentId` ("default" | "claude") used consistently in App.tsx; runtime agent keys `default`/`claude` (Task 7) match the frontend `agentId` values (Task 6); route paths `/openai` `/anthropic` (Task 3) match the runtime `HttpAgent` URLs (Task 7).
