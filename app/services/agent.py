from collections.abc import AsyncGenerator

from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

from app.core.config import settings

# Set the OpenAI API key for the Agents SDK
import openai
openai.api_key = settings.OPENAI_API_KEY

SYSTEM_PROMPT = (
    "You are a friendly, knowledgeable AI assistant. "
    "You provide clear, concise, and helpful answers to questions. "
    "When you are unsure about something, you say so honestly."
)

agent = Agent(
    name="ChatAssistant",
    instructions=SYSTEM_PROMPT,
)


async def run_agent_streamed(user_message: str) -> AsyncGenerator[str, None]:
    """
    Run the agent in streaming mode and yield text deltas as they arrive.
    """
    result = Runner.run_streamed(agent, input=user_message)

    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            yield event.data.delta
