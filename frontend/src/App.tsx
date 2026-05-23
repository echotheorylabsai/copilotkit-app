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
