# ── L5: open generative UI agent (Sonnet 4.6) ────────────────────────────────
# Additive. Like the a2ui agent, this stays a plain chat agent on the backend.
# The Node CopilotRuntime (scoped to this agent in frontend/server.ts) injects the
# capability tools via middleware:
#   - the Excalidraw MCP-app tools (diagrams / whiteboards), and
#   - the open-generative-UI tool (arbitrary interactive HTML/CSS/JS widgets),
# exactly like @ag-ui/a2ui-middleware injects `render_a2ui` for the a2ui agent.
# So we define NO tools here — the generative-UI capability is wired runtime-side.

from pydantic_ai import Agent

# Light-touch on purpose — like the L5 lesson, the capability comes from the
# runtime-injected tools (Excalidraw MCP app + open generative UI), not from heavy
# prompt engineering. We only nudge the model toward the right surface per request;
# the user's own wording ("…using excalidraw", "make a card with raining tacos")
# does most of the steering. (Contrast the a2ui agent, whose prompt is heavy only
# because render_a2ui needs an exact payload shape.)
OPEN_GEN_UI_SYSTEM_PROMPT = (
    "You are a helpful assistant that can create rich, interactive UI.\n\n"
    "- For diagrams, whiteboards, or visual layouts (network diagrams, "
    "flowcharts, sketches), use the Excalidraw app.\n"
    "- For custom widgets, cards, or animations, generate the UI directly.\n"
    "- For everything else, just answer normally."
)

open_agent = Agent("anthropic:claude-sonnet-4-6", system_prompt=OPEN_GEN_UI_SYSTEM_PROMPT)
