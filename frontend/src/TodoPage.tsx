import { useState } from "react";
import { z } from "zod";
import { CopilotChat, useAgent, useFrontendTool } from "@copilotkit/react-core/v2";
import { TodoList, Todo } from "./components/todo-list";

// Shared-state todo canvas. Lives on its own /todos route so the frontend tool
// and shared-state wiring stay isolated from the chat agents (they only exist while
// this page is mounted).
export default function TodoPage() {
  const [open, setOpen] = useState(false);

  // Frontend tool: the agent calls this, but it runs in the browser and drives the
  // panel's open/closed state directly.
  useFrontendTool({
    name: "openOrCloseTodos",
    description: "Open or close the todo panel.",
    parameters: z.object({ open: z.boolean() }),
    handler: async ({ open }) => {
      setOpen(open);
      return `Todos are ${open ? "open" : "closed"}.`;
    },
  });

  // Live handle to the agent's shared state.
  const { agent } = useAgent({ agentId: "todo" });
  const todos: Todo[] = agent.state?.todos ?? [];

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <div style={{ flex: 1, minWidth: 0, position: "relative" }}>
        <CopilotChat key="todo" agentId="todo" />
        {!open && (
          <button
            onClick={() => setOpen(true)}
            className="agent-switch"
            style={{ cursor: "pointer", padding: "6px 12px", borderRadius: 6 }}
          >
            Open todos ({todos.length})
          </button>
        )}
      </div>
      {open && (
        <div style={{ width: 360, flexShrink: 0 }}>
          <TodoList
            todos={todos}
            // Push user edits back into shared state; the agent sees them next turn.
            onUpdate={(updated) => agent.setState({ ...(agent.state ?? {}), todos: updated })}
            isRunning={agent.isRunning}
            onClose={() => setOpen(false)}
          />
        </div>
      )}
    </div>
  );
}
