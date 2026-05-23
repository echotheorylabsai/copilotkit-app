import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

// L3 suggestions work on every agent (frontend useComponent tools: pieChart, flightCard).
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

// L4 suggestions need the a2ui agent's tools (get_sales_data + render_a2ui,
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

export function useExampleSuggestions(agentId: string) {
  const suggestions =
    agentId === "a2ui" ? [...L3_SUGGESTIONS, ...A2UI_SUGGESTIONS] : L3_SUGGESTIONS;

  useConfigureSuggestions({
    available: "always",
    suggestions,
  });
}
