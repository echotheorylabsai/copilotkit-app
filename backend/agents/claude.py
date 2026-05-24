# Plain chat agent (Anthropic Haiku).
# The runtime/frontend id "claude" maps to this route (see frontend/src/agents.ts).

from pydantic_ai import Agent

claude_agent = Agent("anthropic:claude-haiku-4-5", system_prompt="You are a helpful assistant")
