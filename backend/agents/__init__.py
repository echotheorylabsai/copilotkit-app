"""Agent registry — single source of truth for the FastAPI routes.

Each agent lives in its own submodule (openai, claude, a2ui, open_gen_ui); this package
aggregates them. `main.py` registers one POST endpoint per `AGENT_ROUTES` entry.
The path is the public contract consumed by frontend/server.ts HttpAgent URLs —
see README "Contracts" for the route ⇆ agent-id ⇆ model map.

Importing this package constructs the Pydantic AI agents, which validates the
OPENAI_API_KEY / ANTHROPIC_API_KEY at import time — so it cannot be imported
without real keys. `backend/test_contracts.py` parses files as text precisely to
stay key-free; keep it that way.
"""

from backend.agents.a2ui import COMPONENT_NAMES, a2ui_agent
from backend.agents.claude import claude_agent
from backend.agents.open_gen_ui import open_agent
from backend.agents.openai import openai_agent

AGENT_ROUTES = {
    "/openai": openai_agent,
    "/anthropic": claude_agent,
    "/a2ui": a2ui_agent,
    "/open": open_agent,
}

__all__ = ["AGENT_ROUTES", "COMPONENT_NAMES"]
