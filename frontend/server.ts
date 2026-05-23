import { serve } from "@hono/node-server";
import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime, createCopilotEndpoint } from "@copilotkit/runtime/v2";
import { AGENTS, A2UI_AGENT_IDS, OPEN_GEN_UI_AGENT_IDS } from "./src/agents";

const runtime = new CopilotRuntime({
  agents: Object.fromEntries(
    AGENTS.map((agent) => [
      agent.id,
      new HttpAgent({ url: process.env[agent.envVar] || agent.defaultUrl }),
    ]),
  ),
  // Scope A2UI injection to ONLY the a2ui agent(s) so default/claude (L2/L3)
  // are untouched. Dropping `agents` here would inject render_a2ui everywhere.
  a2ui: { injectA2UITool: true, agents: [...A2UI_AGENT_IDS] },
  // L5: Excalidraw MCP App, scoped to the open-gen-ui agent only.
  mcpApps: {
    servers: OPEN_GEN_UI_AGENT_IDS.map((agentId) => ({
      type: "http" as const,
      url: "https://mcp.excalidraw.com",
      serverId: "excalidraw",
      agentId,
    })),
  },
  // L5: let the agent generate arbitrary HTML/CSS/JS. Scoped (not `true`) so
  // default/claude/a2ui are untouched.
  openGenerativeUI: { agents: [...OPEN_GEN_UI_AGENT_IDS] },
});

const app = createCopilotEndpoint({
  runtime,
  basePath: "/api/copilotkit",
});

serve({ fetch: app.fetch, port: 4002 }, () => {
  console.log("CopilotKit API server running at http://localhost:4002");
});
