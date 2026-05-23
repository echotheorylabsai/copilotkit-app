"""L6 — shared-state todo agent (Claude Haiku).

Ports the LangGraph L6 notebook concept to Pydantic AI. The agent and the frontend
share one typed state object (`TodoState`); the AG-UI protocol syncs both sides each
turn:

- Frontend → backend: the UI sends its state in `RunAgentInput.state`; `StateDeps`
  validates it and injects it as `ctx.deps.state`.
- Backend → frontend: a tool emits a `STATE_SNAPSHOT` event by returning it in
  `ToolReturn.metadata`. Unlike LangGraph (which auto-emits on `Command(update=...)`),
  Pydantic AI is opt-in — this metadata channel is the equivalent.
"""

from __future__ import annotations

import uuid

from ag_ui.core import EventType, StateSnapshotEvent
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.ui import StateDeps


class Todo(BaseModel):
    id: str = ""
    title: str
    completed: bool = False


class TodoState(BaseModel):
    todos: list[Todo] = []


todo_agent = Agent(
    "anthropic:claude-haiku-4-5",
    deps_type=StateDeps[TodoState],
    system_prompt=(
        "You manage a shared todo list. "
        "Use manage_todos to add, edit, or remove todos (it replaces the whole list). "
        "Use get_todos to read the current list before changing it. "
        "When asked to manage todos, call the openOrCloseTodos frontend tool with "
        "open=true first. Keep responses to 1-2 sentences."
    ),
)


@todo_agent.tool
def manage_todos(ctx: RunContext[StateDeps[TodoState]], todos: list[Todo]) -> ToolReturn:
    """Replace the entire todo list. Use this to add, edit, or remove todos."""
    for todo in todos:
        if not todo.id:
            todo.id = str(uuid.uuid4())

    ctx.deps.state.todos = todos
    snapshot = {"todos": [todo.model_dump() for todo in todos]}

    return ToolReturn(
        # Tool result the model sees.
        return_value="Successfully updated todos",
        # STATE_SNAPSHOT pushed to the frontend so agent.state.todos stays in sync.
        metadata=StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=snapshot),
    )


@todo_agent.tool
def get_todos(ctx: RunContext[StateDeps[TodoState]]) -> list[dict]:
    """Get the current todo list."""
    return [todo.model_dump() for todo in ctx.deps.state.todos]
