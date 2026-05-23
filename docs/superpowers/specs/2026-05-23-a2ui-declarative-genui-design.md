# L4 — Additive A2UI (Declarative Generative UI) on Pydantic AI

**Date:** 2026-05-23
**Status:** Approved design — ready for implementation plan
**Goal:** Implement the same features as the L4 DeepLearning.AI notebook (dynamic + fixed declarative generative UI via A2UI) in this repo, **additively** (no regression to existing L2/L3 behavior), using **Pydantic AI** agents and **Claude** instead of the notebook's LangGraph + GPT/Gemini stack.

---

## 1. Context: what already exists

This repo is a runnable port of the DeepLearning.AI CopilotKit course:

- **L2** — `backend/main.py` exposes two Pydantic AI agents over AG-UI via `AGUIAdapter.dispatch_request` at `POST /openai` and `POST /anthropic`. `frontend/server.ts` runs a Node `CopilotRuntime` registering both as generic `@ag-ui/client` `HttpAgent`s (`default`, `claude`). React frontend has an agent switcher.
- **L3** — `frontend/src/App.tsx` registers two **controlled** gen-UI components with `useComponent` (`flightCard`, `pieChart`). These are *frontend tools*: the agent calls them over AG-UI; the backend agents have **no backend tools**.

**Key existing facts (verified):**
- `backend/agents.py` constructs two `Agent(...)` at import; both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` must be present for the backend to start (pydantic-ai validates keys at construction).
- Backend runs on port 8002; Node runtime on 4002; Vite on 3002. (`npm run dev` orchestrates all three.)
- pydantic-ai `1.102.0`; `@copilotkit/*` `1.57.4`.

---

## 2. Decisions (locked)

| Decision | Choice |
|---|---|
| Isolation | **New dedicated `a2ui` agent** + new route + new switcher entry. `default`/`claude` agents and L3 components stay untouched. |
| Scope | **Both** A2UI paths (dynamic + fixed), **full 16-component catalog** ported from the notebook. |
| Model | `anthropic:claude-sonnet-4-6` for the `a2ui` agent. |

---

## 3. How A2UI actually works here (verified against installed source)

A2UI is implemented as a **Node-side AG-UI middleware** (`@ag-ui/a2ui-middleware@0.0.5`, a dependency of `@copilotkit/runtime`), auto-applied by `CopilotRuntime` to **any** AG-UI agent when the `a2ui` option is set. The React renderer is `@copilotkit/a2ui-renderer@1.57.4`. Both are already installed. **The Pydantic backend therefore stays thin.**

Source-verified contracts:

- **Dynamic path** — middleware injects a frontend tool named **`render_a2ui`** (`RENDER_A2UI_TOOL_NAME`) with structured parameters `{ surfaceId, catalogId, components, ... }`, **and injects A2UI usage guidelines into the agent context automatically** (`a2ui-middleware/dist/index.d.ts:118,129,131`). Pydantic AI delivers this injected frontend tool to the agent via `_AGUIFrontendToolset(ExternalToolset)` built from `run_input.tools` (`pydantic_ai/ui/ag_ui/_adapter.py:129,282`). The agent's tool-call **arguments stream token-by-token** as native `ToolCallArgsEvent(delta=...)` (`pydantic_ai/ui/ag_ui/_event_stream.py:211,218`), so the dynamic surface renders progressively — **no Python-side streaming middleware needed.**
- **Fixed path** — the middleware inspects `TOOL_CALL_RESULT` events and parses the tool result **content**; if the parsed JSON contains the key **`a2ui_operations`** (constant `g = "a2ui_operations"`) as an array, it renders those operations (`a2ui-middleware/dist/index.mjs`, function `q`). Double-encoded JSON is tolerated. A Pydantic `@agent.tool` returning the envelope dict satisfies this directly.

Per-operation object shapes (`a2ui-middleware/dist/index.d.ts:90-113`, `A2UIMessage`):

```jsonc
{ "createSurface":   { "surfaceId": "...", "catalogId": "...", "theme?": {}, "attachDataModel?": true } }
{ "updateComponents":{ "surfaceId": "...", "components": [ /* flat component array */ ] } }
{ "updateDataModel": { "surfaceId": "...", "path?": "/", "value?": { /* runtime data */ } } }
{ "deleteSurface":   { "surfaceId": "..." } }
```

Catalog id must match between the frontend catalog and the backend fixed-path `createSurface`. Use the notebook value: `copilotkit://app-dashboard-catalog`.

---

## 4. Architecture — files touched

All additions are new files or net-new additions to shared config. No existing L2/L3 logic is rewritten.

```
backend/
  agents.py   ADD: a2ui_agent (anthropic:claude-sonnet-4-6) + 3 @agent.tool fns   [existing 2 agents untouched]
  a2ui.py     NEW: ~20-line envelope builder (no copilotkit/langgraph dependency)
  main.py     ADD: POST /a2ui route via AGUIAdapter.dispatch_request             [existing routes untouched]
frontend/
  src/catalog/definitions.ts   NEW: 16-component Zod catalog (port from notebook)
  src/catalog/renderers.tsx     NEW: React renderers (port; recharts already installed)
  server.ts    ADD: a2ui HttpAgent (-> :8002/a2ui) + `a2ui: { injectA2UITool: true }`  [existing agents untouched]
  src/main.tsx ADD: `a2ui={{ catalog: demonstrationCatalog }}` on <CopilotKit>
  src/App.tsx  ADD: "A2UI (Sonnet 4.6)" switcher option (agentId "a2ui")
  src/hooks/use-example-suggestions.ts  ADD: "Sales Dashboard" + "Display flight information" suggestions
```

---

## 5. Component contracts (the units, their interface, their deps)

### 5.1 `backend/a2ui.py` (NEW) — envelope builder
Pure functions, no external deps. Replicates what the notebook's langgraph-coupled `copilotkit.a2ui` helper produces, in middleware-exact shapes from §3.

```python
_V = "v0.9"  # protocol version; harmless extra key (renderer does not validate it — verified)

def create_surface(surface_id: str, catalog_id: str) -> dict:
    return {"version": _V, "createSurface": {"surfaceId": surface_id, "catalogId": catalog_id}}

def update_components(surface_id: str, components: list[dict]) -> dict:
    return {"version": _V, "updateComponents": {"surfaceId": surface_id, "components": components}}

def update_data_model(surface_id: str, value: dict, path: str = "/") -> dict:
    return {"version": _V, "updateDataModel": {"surfaceId": surface_id, "path": path, "value": value}}

def render(operations: list[dict]) -> dict:
    return {"a2ui_operations": operations}   # detected by @ag-ui/a2ui-middleware (key constant g="a2ui_operations")
```

> **`version` field:** verified that the fixed-path middleware (`createA2UIActivityEvents`) passes operations through unchanged and the renderer does not read a `version` key, so it is **not strictly required**. It is added defensively because the documented A2UI v0.9 protocol states every message must include it, and the parser ignores the extra key.

- **What it does:** builds the `a2ui_operations` envelope.
- **Interface:** four pure functions returning dicts.
- **Depends on:** nothing.

### 5.2 `backend/agents.py` (ADD) — the `a2ui` agent + tools
- `a2ui_agent = Agent("anthropic:claude-sonnet-4-6", system_prompt=...)`.
- Tools — all three are context-free, so use **`@a2ui_agent.tool_plain`** (no `RunContext` parameter):
  - `get_sales_data() -> str` — returns the notebook's sales JSON (revenue, customers, conversion, revenueByCategory, monthlySales).
  - `search_flights(origin: str, destination: str) -> list[Flight]` — returns the notebook's 4 placeholder flights (TypedDict `Flight`).
  - `display_flights(flights: list[Flight]) -> dict` — returns
    `a2ui.render([a2ui.create_surface(SURFACE_ID, CATALOG_ID), a2ui.update_components(SURFACE_ID, FLIGHT_SCHEMA), a2ui.update_data_model(SURFACE_ID, {"flights": flights})])`.
- `SURFACE_ID = "flight-search-results"`, `CATALOG_ID = "copilotkit://app-dashboard-catalog"`.
- `FLIGHT_SCHEMA` — the notebook's fixed component tree, ported verbatim (flat array of `{id, component, ...}` nodes).
- **System prompt** carries tool-routing guidance only (which data tool to call first; use `display_flights` for flights, `render_a2ui` for open-ended dashboards; do not restate data in text). The A2UI *protocol* guidelines are injected by the Node middleware — do not duplicate them.
- **`display_flights` return path (how the dict reaches the middleware):** a `@tool_plain` returning a `dict` is JSON-serialized by Pydantic AI (`model_response_str` → `dump_json`) into the `ToolReturnPart` content, which becomes the AG-UI `TOOL_CALL_RESULT.content` string the middleware parses for the `a2ui_operations` key. Returning the dict directly is sufficient — **do not** wrap it in `ToolReturn(metadata=[CustomEvent(...)])`: a `CustomEvent` is emitted as a raw AG-UI event and bypasses the middleware's `TOOL_CALL_RESULT` parsing entirely (different mechanism — would not render via the catalog). If detection ever fails, the problem is serialization/encoding of the result content, not the mechanism.

> **Construction-time key gotcha:** adding a third agent does not change the existing requirement that both provider keys be present at import. The `a2ui` agent uses Anthropic, already required by the `claude` agent — no new env var.

### 5.3 `backend/main.py` (ADD) — route
```python
@app.post("/a2ui")
async def a2ui_endpoint(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=a2ui_agent)
```

### 5.4 `frontend/src/catalog/definitions.ts` (NEW)
Port the notebook's `demonstrationCatalogDefinitions` (16 components: Title, Text, Icon, Image, Divider, Card, List, Tabs, Row, Column, DashboardCard, Metric, PieChart, BarChart, Badge, DataTable, Button) with their Zod prop schemas. Export `DemonstrationCatalogDefinitions` type.

### 5.5 `frontend/src/catalog/renderers.tsx` (NEW)
Port the notebook's `demonstrationCatalogRenderers` (typed `CatalogRenderers<DemonstrationCatalogDefinitions>` from `@copilotkit/a2ui-renderer`), using `recharts` for Pie/Bar. Assemble and export:
```ts
export const demonstrationCatalog = createCatalog(
  demonstrationCatalogDefinitions, demonstrationCatalogRenderers,
  { catalogId: "copilotkit://app-dashboard-catalog", includeBasicCatalog: false },
);
```

### 5.6 `frontend/server.ts` (ADD)
- Add `const a2uiAgent = new HttpAgent({ url: process.env.A2UI_AGENT_URL || "http://localhost:8002/a2ui" });`
- Register under `agents: { default, claude, a2ui: a2uiAgent }`.
- Add runtime option **`a2ui: { injectA2UITool: true, agents: ["a2ui"] }`**.

> **The `agents: ["a2ui"]` scope is required, not optional.** Verified in `@copilotkit/runtime/dist/v2/runtime/handlers/shared/agent-utils.mjs:26-27`: the runtime destructures `agents: targetAgents` from the `a2ui` option and applies `A2UIMiddleware` only when `targetAgents.includes(agentId)`. Omitting it injects `render_a2ui` + guidelines into **every** agent (`default`, `claude`), which is the primary L2/L3 regression vector. Scoping to `["a2ui"]` eliminates that risk at the source. (`agents?: string[]` is part of the config type — `runtime.d.mts:18`.)

### 5.7 `frontend/src/main.tsx` (ADD)
Add `a2ui={{ catalog: demonstrationCatalog }}` prop to the existing `<CopilotKit>` (import `demonstrationCatalog` from `./catalog/renderers`). Nothing else changes.

> **Schema flow:** the catalog's component schemas are sent to the agent as context from this **React `a2ui={{ catalog }}` prop** (the provider's `includeSchema` defaults to `true`), *not* from a `schema` field in `server.ts`. So the catalog is registered once here and both the renderer and the agent-side schema derive from it.

### 5.8 `frontend/src/App.tsx` (ADD)
- Extend `AgentId` to `"default" | "claude" | "a2ui"`.
- Add `<option value="a2ui">A2UI (Sonnet 4.6)</option>`.
- Keep the existing `useComponent` registrations (L3) and `useExampleSuggestions()` unchanged.

### 5.9 `frontend/src/hooks/use-example-suggestions.ts` (ADD)
Append two suggestions to the existing array: "Sales Dashboard" and "Display flight information". (Single shared suggestions hook; additive only.)

---

## 6. Data flow

**Dynamic (Sales Dashboard):**
```
user → a2ui agent → get_sales_data (backend tool) → agent calls render_a2ui (injected frontend tool)
     → ToolCallArgsEvent deltas stream → a2ui-middleware + a2ui-renderer draw the dashboard
```

**Fixed (Display flight information):**
```
user → a2ui agent → search_flights (backend tool) → display_flights (backend tool returns {a2ui_operations:[...]})
     → TOOL_CALL_RESULT content parsed by a2ui-middleware (key "a2ui_operations") → renderer draws the carousel
```

---

## 7. Verification gates (resolve at implementation, not assumed)

- **A1 — fixed-path detection (empirical run check):** The mechanism is verified in source — the middleware reads `TOOL_CALL_RESULT.content` for key `a2ui_operations`, and Pydantic JSON-serializes the dict return into that content (§5.2). The remaining check is purely runtime: send "Display flight information" and confirm the carousel renders. If it doesn't, inspect the actual `TOOL_CALL_RESULT.content` on the wire (serialization), **not** the mechanism — and do **not** reach for `CustomEvent` (see §5.2).
- **A2 — regression: eliminated by scoping, then verify.** With `agents: ["a2ui"]` (§5.6), `render_a2ui` is injected **only** into the `a2ui` agent — `default`/`claude` are untouched. Verification is now a confirmation, not a risk: after wiring, exercise an L3 prompt on `default`/`claude` and confirm `flightCard`/`pieChart` still render and no `render_a2ui` tool appears.
- **A3 — generation quality (not capability):** Confirm `claude-sonnet-4-6` emits valid A2UI trees for the dynamic dashboard with the middleware-injected guidelines. Capability is proven; this is a prompt-tuning check.

---

## 8. Success criteria

1. **No L2/L3 regression:** switcher still offers `default` + `claude`; both still chat; `flightCard` and `pieChart` `useComponent` renders still work. (Verify by running all three services and exercising L3 prompts.)
2. **Dynamic:** selecting the `a2ui` agent and sending "Sales Dashboard" renders a dashboard (metrics + charts) that **streams in**.
3. **Fixed:** "Display flight information" renders the fixed flight-card carousel populated with the placeholder flight data.
4. Backend starts cleanly on :8002 with `/openai`, `/anthropic`, `/a2ui` all live.

---

## 9. Explicitly out of scope (YAGNI)

- No port of the LangGraph `CopilotKitMiddleware` to Python (the Node middleware covers it).
- No `pip install copilotkit` (pulls langgraph/langchain unnecessarily).
- No interactivity wiring for A2UI `Button` `action` events beyond what the renderer provides by default (notebook parity only).
- No new env vars, ports, or build tooling.
