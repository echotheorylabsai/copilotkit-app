from pydantic_ai import Agent

# Mirrors the notebook's two create_agent() calls — same system prompt, Pydantic AI style.
openai_agent = Agent("openai:gpt-4.1", system_prompt="You are a helpful assistant")
claude_agent = Agent("anthropic:claude-haiku-4-5", system_prompt="You are a helpful assistant")
