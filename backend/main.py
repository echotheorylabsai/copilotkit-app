from dotenv import load_dotenv

load_dotenv()  # load OPENAI_API_KEY / ANTHROPIC_API_KEY from .env

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from pydantic_ai.ui.ag_ui import AGUIAdapter

from backend.agents import openai_agent, claude_agent, a2ui_agent

app = FastAPI()


@app.post("/openai")
async def openai_endpoint(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=openai_agent)


@app.post("/anthropic")
async def anthropic_endpoint(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=claude_agent)


@app.post("/a2ui")
async def a2ui_endpoint(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=a2ui_agent)
