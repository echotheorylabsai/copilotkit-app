from dotenv import load_dotenv

load_dotenv()  # load OPENAI_API_KEY / ANTHROPIC_API_KEY from .env

from fastapi import FastAPI
from pydantic_ai import Agent
from starlette.requests import Request
from starlette.responses import Response
from pydantic_ai.ui.ag_ui import AGUIAdapter

from backend.agents import AGENT_ROUTES

app = FastAPI()


def _make_endpoint(agent: Agent):
    async def endpoint(request: Request) -> Response:
        return await AGUIAdapter.dispatch_request(request, agent=agent)

    return endpoint


# One POST route per agent, driven by the registry in backend/agents/__init__.py.
for path, agent in AGENT_ROUTES.items():
    app.add_api_route(path, _make_endpoint(agent), methods=["POST"])
