// Single source of truth for the agent lineup.
//
// Consumed by three places that previously each hardcoded the list:
//   - App.tsx              → dropdown options + the AgentId type
//   - server.ts            → CopilotRuntime agents map + a2ui middleware scope
//   - use-example-suggestions.ts → which agents get the L4 suggestions
//
// This module is pure data (no React, no process.env reads), so it is safe to
// import from both the browser bundle and the Node runtime. `server.ts` is the
// only consumer that reads `envVar`/`defaultUrl`; the browser only needs id/label.
//
// `id` is the CopilotKit/runtime agent key (must match `agentId` on <CopilotChat>
// and the keys in server.ts). `defaultUrl` points at the FastAPI route the
// runtime proxies to — see the "Contracts" section in README.md for the full
// id ⇆ route ⇆ model mapping.

export const AGENTS = [
  {
    id: "claude",
    label: "Claude (haiku-4-5)",
    envVar: "CLAUDE_AGENT_URL",
    defaultUrl: "http://localhost:8002/anthropic",
    a2ui: false,
    openGenUi: false,
  },
  {
    id: "default",
    label: "OpenAI (gpt-4.1)",
    envVar: "OPENAI_AGENT_URL",
    defaultUrl: "http://localhost:8002/openai",
    a2ui: false,
    openGenUi: false,
  },
  {
    id: "a2ui",
    label: "A2UI (Sonnet 4.6)",
    envVar: "A2UI_AGENT_URL",
    defaultUrl: "http://localhost:8002/a2ui",
    a2ui: true,
    openGenUi: false,
  },
  {
    id: "open",
    label: "Open Gen UI (Sonnet 4.6)",
    envVar: "OPEN_AGENT_URL",
    defaultUrl: "http://localhost:8002/open",
    a2ui: false,
    openGenUi: true,
  },
  {
    // L6 shared-state todo agent. `page: true` keeps it OUT of the L2–L5 chat
    // dropdown (it lives on its own /todos route) while still being wired into the
    // runtime by server.ts, which maps over the full AGENTS list.
    id: "todo",
    label: "Todos (L6)",
    envVar: "TODO_AGENT_URL",
    defaultUrl: "http://localhost:8002/todos",
    a2ui: false,
    openGenUi: false,
    page: true,
  },
] as const;

export type AgentId = (typeof AGENTS)[number]["id"];

/** Agent selected on first load (matches the original default). */
export const DEFAULT_AGENT_ID: AgentId = "claude";

/** Agents shown in the L2–L5 chat dropdown (everything except dedicated-page agents). */
export const DROPDOWN_AGENTS = AGENTS.filter((a) => !("page" in a && a.page));

/** Agent ids that receive A2UI middleware injection + the L4 suggestions. */
export const A2UI_AGENT_IDS: readonly AgentId[] = AGENTS.filter((a) => a.a2ui).map(
  (a) => a.id,
);

/** Agent ids that receive the L5 Excalidraw MCP App + open-generative-UI middleware. */
export const OPEN_GEN_UI_AGENT_IDS: readonly AgentId[] = AGENTS.filter(
  (a) => a.openGenUi,
).map((a) => a.id);
