import { serve } from "@hono/node-server";
import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime, createCopilotEndpoint } from "@copilotkit/runtime/v2";

const openaiAgent = new HttpAgent({
  url: process.env.OPENAI_AGENT_URL || "http://localhost:8002/openai",
});

const claudeAgent = new HttpAgent({
  url: process.env.CLAUDE_AGENT_URL || "http://localhost:8002/anthropic",
});

const a2uiAgent = new HttpAgent({
  url: process.env.A2UI_AGENT_URL || "http://localhost:8002/a2ui",
});

const runtime = new CopilotRuntime({
  agents: {
    default: openaiAgent,
    claude: claudeAgent,
    a2ui: a2uiAgent,
  },
  // Scope A2UI injection to ONLY the a2ui agent so default/claude (L2/L3) are untouched.
  a2ui: { injectA2UITool: true, agents: ["a2ui"] },
});

const app = createCopilotEndpoint({
  runtime,
  basePath: "/api/copilotkit",
});

serve({ fetch: app.fetch, port: 4002 }, () => {
  console.log("CopilotKit API server running at http://localhost:4002");
});
