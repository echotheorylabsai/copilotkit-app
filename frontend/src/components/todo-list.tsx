// Todo panel. Pure presentational component: it reads the shared `todos` array
// and reports user edits back through `onUpdate` (which the page wires to
// `agent.setState`). The backend agent and this panel are two writers of the same
// shared state.

export type Todo = {
  id: string;
  title: string;
  completed: boolean;
};

type TodoListProps = {
  todos: Todo[];
  onUpdate: (todos: Todo[]) => void;
  isRunning: boolean;
  onClose: () => void;
};

export function TodoList({ todos, onUpdate, isRunning, onClose }: TodoListProps) {
  const toggle = (id: string) =>
    onUpdate(
      todos.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t)),
    );

  const remove = (id: string) => onUpdate(todos.filter((t) => t.id !== id));

  const remaining = todos.filter((t) => !t.completed).length;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        borderLeft: "1px solid var(--border)",
        background: "var(--surface)",
        color: "var(--fg)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div style={{ fontWeight: 600 }}>
          Todos{" "}
          <span style={{ color: "var(--muted)", fontWeight: 400 }}>
            ({remaining} left{isRunning ? " · syncing…" : ""})
          </span>
        </div>
        <button
          onClick={onClose}
          style={{ border: "none", background: "none", cursor: "pointer", fontSize: 18, color: "var(--muted)" }}
          aria-label="Close todos"
        >
          ×
        </button>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: 8 }}>
        {todos.length === 0 ? (
          <div style={{ color: "var(--muted)", fontSize: 14, padding: 16, textAlign: "center" }}>
            No todos yet. Ask the agent to add some.
          </div>
        ) : (
          todos.map((todo) => (
            <div
              key={todo.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 12px",
                marginBottom: 6,
                background: "var(--surface-raised)",
                border: "1px solid var(--border)",
                borderRadius: 8,
              }}
            >
              <input
                type="checkbox"
                checked={todo.completed}
                onChange={() => toggle(todo.id)}
              />
              <span
                style={{
                  flex: 1,
                  fontSize: 14,
                  textDecoration: todo.completed ? "line-through" : "none",
                  color: todo.completed ? "var(--muted)" : "var(--fg)",
                }}
              >
                {todo.title}
              </span>
              <button
                onClick={() => remove(todo.id)}
                style={{ border: "none", background: "none", cursor: "pointer", color: "var(--muted)", fontSize: 16 }}
                aria-label="Remove todo"
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
