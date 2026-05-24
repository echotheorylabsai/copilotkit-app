import { useConfigureSuggestions } from "@copilotkit/react-core/v2";
import { A2UI_AGENT_IDS, OPEN_GEN_UI_AGENT_IDS, AgentId } from "../agents";

// These suggestions work on every agent (frontend useComponent tools: pieChart, flightCard).
const L3_SUGGESTIONS = [
  {
    title: "Show my name",
    message: "Show my name in a card. My name is Alex.",
  },
  {
    title: "Pie chart",
    message: "Show a pie chart of revenue by category: Software 40%, Services 35%, Hardware 25%",
  },
  {
    title: "Flight card",
    message: "Show a flight card for Pacific Air from SFO to JFK departing at 08:30 for $249",
  },
];

// A2UI suggestions need the a2ui agent's tools (get_sales_data + render_a2ui,
// search_flights + display_flights). They no-op on default/claude, so only
// surface them when the a2ui agent is selected.
const A2UI_SUGGESTIONS = [
  {
    title: "Sales Dashboard",
    message: "Show me a sales dashboard with total revenue, new customers, and conversion rate metrics.",
  },
  {
    title: "Display flight information",
    message: "Display flight information for flights from SFO to JFK.",
  },
];

// Open-gen-UI suggestions need the open-gen-ui agent's Excalidraw MCP App + open
// generative UI middleware. They no-op on the other agents, so only surface
// them when the open agent is selected.
const OPEN_GEN_UI_SUGGESTIONS = [
  {
    title: "Network diagram",
    message: "Show me a simple network diagram of three routers, two laptops and a server using excalidraw",
  },
  {
    title: "Make it rain tacos",
    message: "Make a card with an animation of raining taco emojis",
  },
];

export function useExampleSuggestions(agentId: AgentId) {
  const suggestions = A2UI_AGENT_IDS.includes(agentId)
    ? [...L3_SUGGESTIONS, ...A2UI_SUGGESTIONS]
    : OPEN_GEN_UI_AGENT_IDS.includes(agentId)
      ? [...L3_SUGGESTIONS, ...OPEN_GEN_UI_SUGGESTIONS]
      : L3_SUGGESTIONS;

  useConfigureSuggestions({
    available: "always",
    suggestions,
    // Scope this config to the selected agent. This hook runs in <App>, OUTSIDE
    // <CopilotChat>, so useConfigureSuggestions has no chat-configuration context
    // to read the agent from — it falls back to the library's DEFAULT_AGENT_ID
    // ("default"). On first load, agents are still being discovered async, so the
    // "reload all agents" path finds none and only reloads that fallback id —
    // which happens to be our OpenAI agent. Binding to `agentId` reloads the
    // right agent immediately and re-runs on every switch.
    consumerAgentId: agentId,
  });
}
