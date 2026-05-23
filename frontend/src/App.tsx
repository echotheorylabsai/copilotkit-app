import { useState } from "react";
import { CopilotChat } from "@copilotkit/react-core/v2";
import { useComponent } from "@copilotkit/react-core/v2";
import { FlightCard, FlightCardProps } from "./components/flight-card";
import { PieChart, PieChartProps } from "./components/pie-chart";
import { useExampleSuggestions } from "./hooks/use-example-suggestions";

type AgentId = "default" | "claude" | "a2ui";

export default function App() {
  const [agentId, setAgentId] = useState<AgentId>("claude");

  useExampleSuggestions(agentId);

  useComponent({
    name: "flightCard",
    description: "Displays a flight summary card with airline, route, departure time, and price.",
    parameters: FlightCardProps,
    render: FlightCard,
  });

  useComponent({
    name: "pieChart",
    description: "Displays data as a pie chart. Use when the user asks for a chart, graph, or visual breakdown of data.",
    parameters: PieChartProps,
    render: PieChart,
  });

  return (
    <div style={{ height: "100%", position: "relative" }}>
      <select
        className="agent-switch"
        value={agentId}
        onChange={(e) => setAgentId(e.target.value as AgentId)}
      >
        <option value="claude">Claude (haiku-4-5)</option>
        <option value="default">OpenAI (gpt-4.1)</option>
        <option value="a2ui">A2UI (Sonnet 4.6)</option>
      </select>
      <CopilotChat key={agentId} agentId={agentId} />
    </div>
  );
}
