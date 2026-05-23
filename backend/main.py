from dotenv import load_dotenv

load_dotenv()  # load OPENAI_API_KEY / ANTHROPIC_API_KEY from .env

from fastapi import FastAPI
from pydantic_ai import Agent
from starlette.requests import Request
from starlette.responses import Response
from pydantic_ai.ui.ag_ui import AGUIAdapter

from typing import Any, Callable

from backend.agents import AGENT_DEPS, AGENT_ROUTES

app = FastAPI()


def _make_endpoint(agent: Agent, deps_factory: Callable[[], Any] | None = None):
    async def endpoint(request: Request) -> Response:
        # Fresh deps per request (StateDeps holds mutable per-conversation state).
        deps = deps_factory() if deps_factory else None
        return await AGUIAdapter.dispatch_request(request, agent=agent, deps=deps)

    return endpoint


# One POST route per agent, driven by the registry in backend/agents/__init__.py.
for path, agent in AGENT_ROUTES.items():
    app.add_api_route(
        path, _make_endpoint(agent, AGENT_DEPS.get(path)), methods=["POST"]
    )
