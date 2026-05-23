# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A demo chat app: React/CopilotKit frontend ⇄ Node CopilotRuntime ⇄ Python FastAPI
serving four Pydantic AI agents, all over the **AG-UI protocol**. It demonstrates
progressively richer generative UI ("levels"):

- **L2** — plain chat (OpenAI `default`, Claude `claude` agents).
- **L3** — frontend-defined tools rendered as React components (`useComponent` in
  `App.tsx`: `flightCard`, `pieChart`). Works on every agent.
- **L4** — declarative A2UI: the agent emits a component *schema* + data, the
  frontend catalog renders it. Only the `a2ui` agent (Sonnet 4.6).
- **L5** — open generative UI: the `open` agent (Sonnet 4.6) gets two
  runtime-injected, **scoped** capabilities — the Excalidraw MCP App and
  `openGenerativeUI` (arbitrary HTML/CSS/JS rendered in a sandboxed iframe). The
  backend agent stays tool-less; the capability is wired in `frontend/server.ts`.

## Commands

```bash
uv sync                       # Python deps → .venv
npm install && npm --prefix frontend install   # Node deps (two package.json's)
cp .env-template .env         # then set OPENAI_API_KEY + ANTHROPIC_API_KEY

npm run dev                   # all three processes (concurrently)
npm run backend               # just FastAPI agents  :8002
npm run runtime               # just CopilotRuntime   :4002
npm run frontend              # just Vite             :3002

npm test                      # contract test (uv run python -m backend.test_contracts)
npm --prefix frontend run build   # Vite build only (no tsc); run `npx tsc --noEmit` to type-check
```

There is no test framework beyond the single contract guard; `npm test` runs it
directly. Run it after touching A2UI component names (see below).

## Architecture: request flow

```
Browser (:3002, Vite proxy /api/copilotkit → :4002)
  └─ CopilotKit React, agentId from dropdown
       └─ CopilotRuntime (Node/Hono, server.ts, :4002)
            └─ HttpAgent → FastAPI route (:8002)
                 └─ AGUIAdapter.dispatch_request → Pydantic AI Agent
```

- **Backend** (`backend/main.py`): registers one POST route per entry in
  `AGENT_ROUTES` (`backend/agents/__init__.py`), each dispatched through `AGUIAdapter`.
  Each agent lives in its own submodule (`backend/agents/openai.py`, `claude.py`,
  `a2ui.py`, `open_gen_ui.py`); the package `__init__.py` aggregates them into
  `AGENT_ROUTES`.
- **Runtime** (`frontend/server.ts`): maps each `AGENTS` entry to an `HttpAgent`
  pointing at its FastAPI route. Three middlewares are **scoped** so they only
  attach to the agents that should have them — unscoping any of them injects its
  tools into every agent and breaks the other levels:
  - `@ag-ui/a2ui-middleware` → `A2UI_AGENT_IDS` (injects `render_a2ui`, L4).
  - `mcpApps` (Excalidraw) and `openGenerativeUI` → `OPEN_GEN_UI_AGENT_IDS` (L5).
    These are CopilotRuntime middlewares applied via `agent.use(...)`, so they work
    on the AG-UI `HttpAgent`s with **no backend change**. `mcpApps` scopes via each
    server's `agentId`; `openGenerativeUI` via `{ agents: [...] }` (never `true`).
- **Frontend** (`frontend/src/main.tsx`, `App.tsx`): one `<CopilotChat>` keyed by
  `agentId`; switching the dropdown remounts it.

## Cross-language contracts (read before editing wiring)

Several string constants and lists are shared across the Python/Node boundary with
**nothing enforcing them at compile time** — change one half and the wiring silently
breaks. The full table lives in **README.md → "Contracts"**; consult it before
touching agent ids, routes, catalog/surface ids, or A2UI component names.

Single sources of truth:
- Agent lineup (id ⇆ route ⇆ `a2ui`/`openGenUi` flags): `frontend/src/agents.ts`.
- Route → agent: `AGENT_ROUTES` in `backend/agents/__init__.py`.
- A2UI component names: `COMPONENT_NAMES` in `backend/agents/a2ui.py` **must** equal
  the keys of `demonstrationCatalogDefinitions` in `frontend/src/catalog/definitions.ts`.
  `backend/test_contracts.py` guards exactly this (by text-parsing both files) — it
  reads `backend/agents/a2ui.py`, so keep `COMPONENT_NAMES` a literal list there.

## Key gotchas

- **API keys are required at import, not request, time.** Constructing a Pydantic AI
  `Agent` validates the key, so the `backend/agents` package cannot be imported
  without real `sk-...` keys. This is why `test_contracts.py` parses files as text
  instead of importing the module — keep that test key-free.
- **A2UI needs zod v3.** The renderer's schema scraper (`GenericBinder`) requires
  zod v3; the flight-card declarative data binding (`FLIGHT_SCHEMA` in
  `backend/agents/a2ui.py`) depends on it.
- **Suggestions must set `consumerAgentId`.** `useConfigureSuggestions` runs outside
  `<CopilotChat>`, so without `consumerAgentId` it attaches to the library's
  `"default"` fallback instead of the selected agent (see
  `hooks/use-example-suggestions.ts`).
- **A2UI agent prompt is load-bearing.** `A2UI_SYSTEM_PROMPT` dictates exactly which
  tools to call for flights vs. dashboards and the precise `render_a2ui` component
  shape (flat props, `component` not `type`, no `Box`). Editing it changes behavior.
- **L5 capabilities must stay scoped, and the MCP server is reached at request time.**
  `mcpApps`/`openGenerativeUI` in `server.ts` are scoped to `OPEN_GEN_UI_AGENT_IDS`;
  setting `openGenerativeUI: true` or omitting a server's `agentId` leaks the tools
  into every agent. Unlike A2UI, the `open` agent's prompt is intentionally
  light-touch — the capability comes from the injected tools, not the prompt. At run
  time the runtime makes outbound HTTP to `https://mcp.excalidraw.com` to discover the
  MCP App; if unreachable the tool just doesn't appear (progressive enhancement, no
  crash). The generative-UI iframe runs with `allow-scripts`+`allow-same-origin` — a
  trust surface to note before any non-demo use.

## Before planning any feature change or implementation

Use the `ai-docs` MCP to fetch up-to-date documentation **before** writing a plan or touching code:

```
mcp__ai-docs__list_doc_sources   # see configured sources
mcp__ai-docs__fetch_docs         # fetch CopilotKit or pydantic-ai docs by URL
```

Configured sources: CopilotKit (`https://docs.copilotkit.ai/llms.txt`) and
pydantic-ai (`https://pydantic.dev/docs/validation/latest/llms.txt`). Always prefer
these over training knowledge — both libraries evolve rapidly.

## Notes

- Design specs and implementation plans live in `docs/superpowers/` (gitignored).
- The `default` agent id maps to **OpenAI**, `claude` to Anthropic Haiku — the
  names are historical; don't assume id == provider.
