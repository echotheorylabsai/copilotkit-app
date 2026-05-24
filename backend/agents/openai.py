# Plain chat agent (Pydantic AI style).
# The runtime/frontend id "default" maps to this route (see frontend/src/agents.ts) —
# the id names are historical; don't assume id == provider.

from pydantic_ai import Agent

openai_agent = Agent("openai:gpt-4.1", system_prompt="You are a helpful assistant")
