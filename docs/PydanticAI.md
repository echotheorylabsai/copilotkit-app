# Pydantic AI: RunContext and the AG-UI State Flow

A precise reference for how `RunContext`, `StateDeps`, and `ToolReturn.metadata` wire together in this app. Every claim is sourced from the installed library code under `.venv/`.

---

## 1. What is `RunContext`?

`RunContext` is a **dataclass** (not a Pydantic model) defined in `pydantic_ai/_run_context.py`. Pydantic AI's runtime constructs and populates it before every tool call — you never instantiate it yourself.

```python
@dataclasses.dataclass(repr=False, kw_only=True)
class RunContext(Generic[RunContextAgentDepsT]):
    ...
```

The generic parameter `T` in `RunContext[T]` types only one field: `ctx.deps`. Everything else is always present regardless of `T`.

### Full field reference

| Field | Type | Description |
|---|---|---|
| `ctx.deps` | `T` | Your injected dependencies — in this app, `StateDeps[TodoState]` |
| `ctx.model` | `Model` | The LLM instance running this turn |
| `ctx.usage` | `RunUsage` | Token counts accumulated so far in this run |
| `ctx.agent` | `Agent \| None` | The agent instance itself |
| `ctx.prompt` | `str \| Sequence[UserContent] \| None` | The original user message that triggered the run |
| `ctx.messages` | `list[ModelMessage]` | Full conversation history up to this tool call |
| `ctx.tool_name` | `str \| None` | Name of the currently executing tool |
| `ctx.tool_call_id` | `str \| None` | Unique ID for this specific tool invocation |
| `ctx.retry` | `int` | How many times this tool has retried (0-based) |
| `ctx.max_retries` | `int` | Retry limit for this tool |
| `ctx.last_attempt` | `bool` | Shorthand: `retry == max_retries` (property) |
| `ctx.retries` | `dict[str, int]` | Per-tool retry counts across the whole run |
| `ctx.run_step` | `int` | Which agent loop iteration this is |
| `ctx.run_id` | `str \| None` | Unique ID for the whole agent run |
| `ctx.conversation_id` | `str \| None` | Spans multiple runs sharing message history |
| `ctx.tool_call_approved` | `bool` | Whether a deferred tool call has been approved |
| `ctx.tool_call_metadata` | `Any` | Metadata from `DeferredToolResults`, when approved |
| `ctx.partial_output` | `bool` | Whether an output validator is receiving a partial result |
| `ctx.metadata` | `dict[str, Any] \| None` | Run-level metadata |
| `ctx.model_settings` | `ModelSettings \| None` | Merged model settings for the current step |
| `ctx.validation_context` | `Any` | Pydantic validation context for tool args and output |
| `ctx.pending_messages` | `list[PendingMessage] \| None` | Internal queue for `ctx.enqueue()` |
| `ctx.tool_manager` | `ToolManager \| None` | Access to tool dispatch machinery |
| `ctx.tracer` | `Tracer` | OpenTelemetry tracer for this run |
| `ctx.trace_include_content` | `bool` | Whether to include message content in traces |
| `ctx.instrumentation_version` | `int` | Instrumentation settings version |

### The one method: `ctx.enqueue()`

```python
ctx.enqueue(*content, priority='asap')
```

Injects messages back into the conversation mid-tool without returning them. Useful for streaming partial progress. Raises `UserError` if called outside an active agent run.

---

## 2. What is `StateDeps`?

Defined in `pydantic_ai/ui/_adapter.py`:

```python
@dataclass
class StateDeps(Generic[StateT]):
    state: StateT
```

It is a minimal dataclass with a single field. `StateT` must be a subclass of `BaseModel`. This is how shared state is injected into `ctx.deps` in tools.

`StateDeps` implements the `StateHandler` protocol (also in `_adapter.py`), which requires:
- `__dataclass_fields__` (satisfied automatically by `@dataclass`)
- A `state` property with both getter and setter

The runtime checks `isinstance(deps, StateHandler)` — a structural check, not a class hierarchy check — to decide whether to hydrate state from the frontend request.

---

## 3. What is `ToolReturn`?

Defined in `pydantic_ai/messages.py`:

```python
@dataclass(repr=False)
class ToolReturn(Generic[_ToolReturnValueT]):
    return_value: ToolReturnContent   # what the LLM sees in its tool result
    _: KW_ONLY                        # everything below is keyword-only
    content: str | Sequence[UserContent] | None = None  # injected as a separate UserPromptPart
    metadata: Any = None              # NOT sent to the LLM — application layer only
    kind: Literal['tool-return'] = 'tool-return'
```

The critical distinction: `return_value` is serialised into the tool result message the model reads. `metadata` is invisible to the model — it is an escape hatch for the application layer (e.g., emitting AG-UI events).

---

## 4. State flow: Frontend → Agent

### The path

```
TodoPage.tsx
  agent.setState({ todos: updated })          ← user edits in browser
       │
       ▼
CopilotKit / AG-UI sends HTTP POST to /todos
  body: RunAgentInput { state: { todos: [...] }, messages: [...], ... }
       │
       ▼
main.py: deps = AGENT_DEPS["/todos"]()  →  StateDeps(TodoState())
  └── deps_factory() is called fresh per request          ← mutable state, must not be shared
  └── AGUIAdapter.dispatch_request(request, agent=todo_agent, deps=deps)
       │
       ▼
AGUIAdapter._adapter.py: adapter.state property
  └── reads run_input.state from the parsed RunAgentInput
       │
       ▼
UIAdapter._adapter.py: run_stream_native()
  └── isinstance(deps, StateHandler) → True
  └── type(deps.state).model_validate(raw_state)   ← TodoState.model_validate({"todos": [...]})
  └── deps.state = validated_todo_state             ← overwrites the empty TodoState()
       │
       ▼
pydantic_ai Agent.run_stream_events(deps=deps, ...)
       │
       ▼
Tool is called: manage_todos(ctx, todos)
  └── ctx.deps            → the StateDeps[TodoState] instance
  └── ctx.deps.state      → the hydrated TodoState (from frontend)
  └── ctx.deps.state.todos → list[Todo] sent by the frontend this turn
```

### Key implementation detail

`__init__.py` registers the deps factory as:

```python
AGENT_DEPS = {
    "/todos": lambda: StateDeps(TodoState()),
}
```

`StateDeps(TodoState())` starts with an empty list. The `UIAdapter` then **overwrites** `deps.state` with the validated frontend state before the agent runs. If no state is sent, the empty `TodoState()` is preserved.

---

## 5. State flow: Agent → Frontend

This direction is **opt-in** in Pydantic AI (unlike LangGraph's `Command(update=...)` which auto-emits). The mechanism is `ToolReturn.metadata`.

### The path

```
manage_todos tool body
  ctx.deps.state.todos = todos                    ← mutate in-place (for this request's lifetime)
  return ToolReturn(
      return_value="Successfully updated todos",  ← the string the LLM reads
      metadata=StateSnapshotEvent(                ← invisible to LLM
          type=EventType.STATE_SNAPSHOT,
          snapshot={"todos": [...]}
      ),
  )
       │
       ▼
AGUIEventStream._handle_tool_result() in _event_stream.py
  └── yields ToolCallResultEvent(content=return_value)  ← LLM gets "Successfully updated todos"
  └── checks: result.metadata or result.content
  └── isinstance(possible_event, BaseEvent) → True
  └── yields StateSnapshotEvent directly into the AG-UI stream
       │
       ▼
CopilotKit receives STATE_SNAPSHOT event
  └── agent.state.todos is updated in the browser
  └── TodoPage re-renders with new todos (via useAgent hook)
```

### Why `metadata` and not `return_value`?

If you put the `StateSnapshotEvent` in `return_value`, the LLM would receive a raw serialised event object in its tool result message — confusing and token-wasteful. `metadata` is explicitly documented as "not sent to the LLM", making it the correct channel for protocol-layer side-effects.

---

## 6. Full request lifecycle (end to end)

```
Browser                     Node Runtime              FastAPI / Pydantic AI
──────                      ────────────              ─────────────────────
user edits todo
agent.setState(state)
                ─────POST /api/copilotkit──────────►
                                         ─────POST /todos──────────────────►
                                                       AGUIAdapter.dispatch_request()
                                                       deps = AGENT_DEPS["/todos"]()  # StateDeps(TodoState())
                                                       deps.state = TodoState.model_validate(run_input.state)
                                                       agent.run_stream_events(deps=deps)
                                                         tool: get_todos(ctx)
                                                           └─ ctx.deps.state.todos → [...]
                                                         tool: manage_todos(ctx, todos)
                                                           └─ ctx.deps.state.todos = todos
                                                           └─ return ToolReturn(
                                                                return_value="Successfully updated todos",
                                                                metadata=StateSnapshotEvent)
                                                       _handle_tool_result()
                                                         └─ yield ToolCallResultEvent
                                                         └─ yield StateSnapshotEvent
                ◄─── SSE stream ──────────────────────────────────────────────
agent.state.todos updated
TodoPage re-renders
```

---

## 7. UIAdapter pipeline: from HTTP request to streaming response

`AGUIAdapter.dispatch_request` is the single entry point. It drives a fixed three-layer pipeline — each layer has exactly one job and can be used independently (e.g. `run_stream` alone in tests, without a Starlette response).

### Top-level call sequence

```
POST /todos (FastAPI)
    │
    ▼
AGUIAdapter.dispatch_request(request, agent, deps)    ← classmethod, your entry point
    │
    ├─► from_request(request, agent)
    │       ├─ await request.body()
    │       ├─ build_run_input(bytes) → RunAgentInput  (parse AG-UI JSON)
    │       ├─ request.headers['Accept']               (stored for SSE encoding)
    │       └─► UIAdapter.__init__()                   (adapter instance, one per request)
    │
    ├─► adapter.run_stream(…)                          ← INNER: params → AsyncIterator[EventT]
    │       └─► run_stream_native(…)                   ← agent execution
    │               ├─ sanitize_messages               (strip client system prompts)
    │               ├─ state hydration (§4)            (deps.state = TodoState.model_validate(…))
    │               ├─ inject capabilities             (ReinjectSystemPrompt, etc.)
    │               └─► agent.run_stream_events(…)     → yields NativeEvent
    │           └─► transform_stream(native_events)    ← protocol translation
    │                   NativeEvent ──► EventT (AG-UI)
    │                   ToolCallEvent → ToolCallStart + ToolCallArgs + ToolCallEnd
    │                   TextDelta    → TextMessageChunk
    │                   FinalResult  → RunFinished + on_complete()
    │
    └─► adapter.streaming_response(AsyncIterator[EventT])  ← OUTER: HTTP response
            ├─ build_event_stream()                    (protocol encoder, from Accept header)
            ├─ encode_stream()                         EventT → "data: {…}\n\n"  (SSE)
            └─► Starlette StreamingResponse            (streamed back chunk-by-chunk)
```

### The two `cast()` calls in `dispatch_request`

```python
adapter = cast(
    UIAdapter[RunInputT, MessageT, EventT, DispatchDepsT, DispatchOutputDataT],
    await cls.from_request(
        request,
        agent=cast(AbstractAgent[AgentDepsT, OutputDataT], agent),
        …
    ),
)
```

Both `cast()` calls are **type-checker annotations only** — zero runtime effect. The problem they solve: `from_request` is a `classmethod`, so pyright infers its return type from `cls` (the class-level type params). But the actual concrete types (`DispatchDepsT`, `DispatchOutputDataT`) come from the `agent` argument at the call site. The outer `cast` corrects pyright's inferred return type; the inner `cast` re-states `agent`'s concrete params so pyright doesn't widen them.

### NativeEvent vs EventT

| Type | Owner | Examples |
|---|---|---|
| `NativeEvent` | Pydantic AI internal | `ModelRequestEvent`, `ToolCallEvent`, `FinalResultEvent` |
| `EventT` | Protocol-specific (AG-UI here) | `RunStarted`, `TextMessageChunk`, `ToolCallStart`, `StateSnapshot` |

`transform_stream` is the translation boundary. Each concrete `UIAdapter` subclass provides its own `build_event_stream()` — that is the single abstract method every protocol adapter must implement. Everything else in the pipeline is shared and protocol-agnostic.

### Class responsibility map

```
UIAdapter (ABC)
├── from_request()        classmethod  parse HTTP → adapter instance
├── build_run_input()     abstract     bytes → RunInputT
├── messages              cached_prop  RunInputT → ModelMessage[]
├── state                 cached_prop  RunInputT → dict  (AG-UI state)
├── toolset               cached_prop  RunInputT → frontend tools
│
├── run_stream_native()   agent.run_stream_events() → NativeEvent stream
├── transform_stream()    NativeEvent stream → EventT stream
├── build_event_stream()  abstract     protocol encoder/transformer  ← key extension point
│
└── streaming_response()  EventT stream → Starlette HTTP response
        └── encode_stream()  EventT → str  (SSE / NDJSON, from Accept header)
```

---

## 9. Source locations

| Concept | File |
|---|---|
| `RunContext` | `.venv/.../pydantic_ai/_run_context.py:35` |
| `StateDeps` / `StateHandler` | `.venv/.../pydantic_ai/ui/_adapter.py:80–118` |
| State hydration logic | `.venv/.../pydantic_ai/ui/_adapter.py:519–532` |
| `ToolReturn` | `.venv/.../pydantic_ai/messages.py:886` |
| STATE_SNAPSHOT emission | `.venv/.../pydantic_ai/ui/ag_ui/_event_stream.py:267–278` |
| AG-UI state extraction | `.venv/.../pydantic_ai/ui/ag_ui/_adapter.py:285–295` |
| Agent registry + deps factory | `backend/agents/__init__.py:34–36` |
| Todo agent tools | `backend/agents/todos.py` |
| Frontend state hook | `frontend/src/TodoPage.tsx:25–27` |
